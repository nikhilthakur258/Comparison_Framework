import os
import argparse
from github import Github, GithubException
from datetime import datetime
import time
import xml.etree.ElementTree as ET
import json
import chardet

# Set up GitHub API access
GITHUB_TOKENS = os.getenv('GITHUB_TOKENS')  # Ensure this is set as an environment variable
if not GITHUB_TOKENS:
    raise ValueError("Please set your GITHUB_TOKENS environment variable.")
tokens = GITHUB_TOKENS.split(',')
token_index = 0
g = Github(tokens[token_index])

# Checkpoint file to save progress
CHECKPOINT_FILE = 'checkpoint.json'

def switch_token():
    global token_index, g
    token_index = (token_index + 1) % len(tokens)
    g = Github(tokens[token_index])
    print(f"Switched to token {token_index + 1}")

def check_rate_limit():
    rate_limit = g.get_rate_limit()
    core_limit = rate_limit.core
    reset_time = core_limit.reset.timestamp()  # Convert to timestamp
    remaining = core_limit.remaining
    print(f"Rate limit remaining: {remaining}")
    print(f"Reset time: {datetime.fromtimestamp(reset_time)}")
    return remaining, reset_time

def wait_for_rate_limit_reset():
    while True:
        remaining, reset_time = check_rate_limit()
        if remaining == 0:
            if token_index == len(tokens) - 1:
                wait_time = max(reset_time - time.time(), 0) + 10  # Add a buffer time
                print(f"Rate limit exceeded. Waiting for {wait_time} seconds before retrying...")
                time.sleep(wait_time)
                token_index = 0
            else:
                switch_token()
        else:
            break

def get_repo_info(repo_name):
    while True:
        try:
            repo = g.get_repo(repo_name)
            info = {
                'name': repo.name,
                'description': repo.description,
                'language': repo.language,
                'topics': repo.get_topics(),
                'default_branch': repo.default_branch,
                'size': repo.size,
                'created_at': repo.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': repo.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'subscribers_count': repo.subscribers_count,
                'stargazers_count': repo.stargazers_count,
                'watchers_count': repo.watchers_count,
                'forks_count': repo.forks_count,
                'open_issues_count': repo.open_issues_count,
                'license': repo.license.name if repo.license else 'None',
                'html_url': repo.html_url,
            }
            return info
        except GithubException as e:
            if e.status == 403 and 'rate limit exceeded' in str(e):
                wait_for_rate_limit_reset()
                continue
            else:
                raise ValueError(f"Error fetching repository '{repo_name}': {e}")

def get_files_recursively(repo, path='', extensions=None):
    if extensions is None:
        extensions = []
    result_files = []
    contents = repo.get_contents(path)
    while contents:
        content = contents.pop(0)
        if content.type == 'dir':
            contents.extend(repo.get_contents(content.path))
        else:
            if any(content.name.endswith(ext) for ext in extensions):
                result_files.append(content)
            elif not extensions:  # Add all files if no extensions are specified
                result_files.append(content)
    return result_files

def decode_content(file_content):
    try:
        detected_encoding = chardet.detect(file_content)
        encoding = detected_encoding.get('encoding') or 'utf-8'
        return file_content.decode(encoding, errors='ignore')
    except Exception as e:
        print(f"Error decoding content: {e}. Falling back to 'utf-8'.")
        return file_content.decode('utf-8', errors='ignore')

def count_files(repo_name, extensions):
    while True:
        try:
            repo = g.get_repo(repo_name)
            files = get_files_recursively(repo, '', extensions)
            total_lines = sum(decode_content(f.decoded_content).count('\n') + 1 for f in files)
            return len(files), total_lines
        except GithubException as e:
            if e.status == 403 and 'rate limit exceeded' in str(e):
                wait_for_rate_limit_reset()
                continue
            else:
                raise ValueError(f"Error counting files in repository '{repo_name}': {e}")

def get_file_details(repo_name, extensions):
    while True:
        try:
            repo = g.get_repo(repo_name)
            files = get_files_recursively(repo, '', extensions)
            file_details = []
            for file in files:
                content = decode_content(file.decoded_content)
                lines = content.count('\n') + 1 if content else 0
                file_details.append({
                    'name': file.name,
                    'path': file.path,
                    'size': file.size,
                    'lines_of_code': lines,
                })
            return file_details
        except GithubException as e:
            if e.status == 403 and 'rate limit exceeded' in str(e):
                wait_for_rate_limit_reset()
                continue
            else:
                raise ValueError(f"Error fetching file details from repository '{repo_name}': {e}")
        except Exception as e:
            raise ValueError(f"Error fetching file details from repository '{repo_name}': {e}")

def parse_pom_xml(content):
    root = ET.fromstring(content)
    namespaces = {'maven': 'http://maven.apache.org/POM/4.0.0'}
    dependencies = []
    properties = {}
    java_version = 'N/A'
    spring_boot_version = 'N/A'
    
    for prop in root.findall('.//maven:properties/*', namespaces):
        properties[prop.tag.split('}', 1)[1]] = prop.text
    
    for dependency in root.findall('.//maven:dependency', namespaces):
        group_id_element = dependency.find('maven:groupId', namespaces)
        artifact_id_element = dependency.find('maven:artifactId', namespaces)
        version_element = dependency.find('maven:version', namespaces)
        
        group_id = group_id_element.text if group_id_element is not None else 'N/A'
        artifact_id = artifact_id_element.text if artifact_id_element is not None else 'N/A'
        version = version_element.text if version_element is not None else 'N/A'
        
        if version.startswith('${') and version.endswith('}'):
            prop_name = version[2:-1]
            version = properties.get(prop_name, 'N/A')
        
        dependencies.append({
            'group_id': group_id,
            'artifact_id': artifact_id,
            'version': version
        })

    # Extract Java version
    java_version_element = root.find('.//maven:properties/maven:java.version', namespaces)
    if java_version_element is not None:
        java_version = java_version_element.text

    # Extract Spring Boot version
    parent_version_element = root.find('.//maven:parent/maven:version', namespaces)
    if parent_version_element is not None and 'spring-boot' in root.find('.//maven:parent/maven:artifactId', namespaces).text:
        spring_boot_version = parent_version_element.text

    parent_group_id = root.find('.//maven:parent/maven:groupId', namespaces).text if root.find('.//maven:parent/maven:groupId', namespaces) is not None else 'N/A'
    parent_artifact_id = root.find('.//maven:parent/maven:artifactId', namespaces).text if root.find('.//maven:parent/maven:artifactId', namespaces) is not None else 'N/A'
    parent_version = root.find('.//maven:parent/maven:version', namespaces).text if root.find('.//maven:parent/maven:version', namespaces) is not None else 'N/A'
    parent_name = root.find('.//maven:parent/maven:name', namespaces).text if root.find('.//maven:parent/maven:name', namespaces) is not None else 'N/A'

    group_id = root.find('.//maven:groupId', namespaces).text if root.find('.//maven:groupId', namespaces) is not None else 'N/A'
    artifact_id = root.find('.//maven:artifactId', namespaces).text if root.find('.//maven:artifactId', namespaces) is not None else 'N/A'
    version = root.find('.//maven:version', namespaces).text if root.find('.//maven:version', namespaces) is not None else 'N/A'
    name = root.find('.//maven:name', namespaces).text if root.find('.//maven:name', namespaces) is not None else 'N/A'

    return dependencies, java_version, spring_boot_version, group_id, artifact_id, version, name, parent_group_id, parent_artifact_id, parent_version, parent_name

def parse_gradle_file(content):
    java_version = 'N/A'
    spring_boot_version = 'N/A'
    lines = content.split('\n')
    for line in lines:
        if 'sourceCompatibility' in line or 'targetCompatibility' in line:
            parts = line.split()
            if len(parts) >= 2:
                java_version = parts[-1].replace("'", "").replace("\"", "")
        if 'spring-boot' in line and 'version' in line:
            parts = line.split()
            if len(parts) >= 2:
                spring_boot_version = parts[-1].replace("'", "").replace("\"", "")
    return java_version, spring_boot_version

def parse_package_json(content):
    import json
    package_json = json.loads(content)
    dependencies = package_json.get('dependencies', {})
    dev_dependencies = package_json.get('devDependencies', {})
    
    angular_version = 'N/A'
    node_version = package_json.get('engines', {}).get('node', 'N/A')
    
    if '@angular/core' in dependencies:
        angular_version = dependencies['@angular/core']
    elif '@angular/core' in dev_dependencies:
        angular_version = dev_dependencies['@angular/core']
    
    return angular_version, node_version

def get_dependencies_and_versions(repo_name):
    while True:
        try:
            repo = g.get_repo(repo_name)
            pom_files = get_files_recursively(repo, '', ['pom.xml'])
            gradle_files = get_files_recursively(repo, '', ['build.gradle'])
            package_json_files = get_files_recursively(repo, '', ['package.json'])
            dependencies = []
            java_versions = []
            spring_boot_versions = []
            angular_versions = []
            node_versions = []
            build_tool = 'N/A'
            group_id = artifact_id = version = name = 'N/A'
            parent_group_id = parent_artifact_id = parent_version = parent_name = 'N/A'
            for pom_file in pom_files:
                content = decode_content(repo.get_contents(pom_file.path).decoded_content)
                deps, java_version, spring_boot_version, gid, aid, ver, nm, pgid, paid, pver, pnm = parse_pom_xml(content)
                dependencies.extend(deps)
                if java_version != 'N/A':
                    java_versions.append(java_version)
                if spring_boot_version != 'N/A':
                    spring_boot_versions.append(spring_boot_version)
                build_tool = 'Maven'
                group_id = gid
                artifact_id = aid
                version = ver
                name = nm
                parent_group_id = pgid
                parent_artifact_id = paid
                parent_version = pver
                parent_name = pnm
            for gradle_file in gradle_files:
                content = decode_content(repo.get_contents(gradle_file.path).decoded_content)
                java_version, spring_boot_version = parse_gradle_file(content)
                if java_version != 'N/A':
                    java_versions.append(java_version)
                if spring_boot_version != 'N/A':
                    spring_boot_versions.append(spring_boot_version)
                build_tool = 'Gradle'
            for package_json_file in package_json_files:
                content = decode_content(repo.get_contents(package_json_file.path).decoded_content)
                angular_version, node_version = parse_package_json(content)
                if angular_version != 'N/A':
                    angular_versions.append(angular_version)
                if node_version != 'N/A':
                    node_versions.append(node_version)
                build_tool = 'NPM/Yarn'
            return dependencies, java_versions, spring_boot_versions, angular_versions, node_versions, build_tool, group_id, artifact_id, version, name, parent_group_id, parent_artifact_id, parent_version, parent_name
        except GithubException as e:
            if e.status == 403 and 'rate limit exceeded' in str(e):
                wait_for_rate_limit_reset()
                continue
            else:
                raise ValueError(f"Error fetching dependencies from repository '{repo_name}': {e}")

def analyze_manifest_files(repo_name):
    while True:
        try:
            repo = g.get_repo(repo_name)
            manifest_files = get_files_recursively(repo, '', ['manifest.yml'])
            manifest_details = []
            for manifest_file in manifest_files:
                content = decode_content(manifest_file.decoded_content)
                lines = content.count('\n') + 1 if content else 0
                manifest_details.append({
                    'name': manifest_file.name,
                    'path': manifest_file.path,
                    'size': manifest_file.size,
                    'lines_of_code': lines,
                    'content': content,
                })
            return manifest_details
        except GithubException as e:
            if e.status == 403 and 'rate limit exceeded' in str(e):
                wait_for_rate_limit_reset()
                continue
            else:
                raise ValueError(f"Error fetching manifest files from repository '{repo_name}': {e}")

def search_pcf_references(repo_name):
    while True:
        try:
            repo = g.get_repo(repo_name)
            files = get_files_recursively(repo, '')  # Fetch all files
            pcf_references = []
            for file in files:
                content = decode_content(file.decoded_content).lower()
                lines = content.split('\n')
                for line_number, line in enumerate(lines, start=1):
                    if 'pcf' in line or 'cloudfoundry' in line:
                        print(f"Found PCF reference in file: {file.path}, line: {line_number}")  # Debug log
                        pcf_references.append({
                            'name': file.name,
                            'path': file.path,
                            'size': file.size,
                            'lines_of_code': content.count('\n') + 1,
                            'line_number': line_number,
                            'line_content': line.strip()
                        })
            return pcf_references
        except GithubException as e:
            if e.status == 403 and 'rate limit exceeded' in str(e):
                wait_for_rate_limit_reset()
                continue
            else:
                raise ValueError(f"Error searching PCF references in repository '{repo_name}': {e}")

def calculate_complexity(java_files_count, dependencies_count, config_files_count, pcf_references_count):
    complexity_score = java_files_count + dependencies_count + config_files_count + pcf_references_count
    
    if complexity_score <= 10:
        return "Low"
    elif complexity_score <= 20:
        return "Medium"
    else:
        return "High"

def sanitize_sheet_title(title):
    invalid_chars = ['\\', '/', '*', '[', ']', ':', '?']
    for char in invalid_chars:
        title = title.replace(char, '')
    return title[:31]

def generate_html_report(repo_reports, summary_report, filename):
    tabs = ""
    contents = ""
    
    for index, report in enumerate(repo_reports):
        tab_id = sanitize_sheet_title(report["repo_name"] + str(index))
        tabs += f'<button class="tablinks" onclick="openTab(event, \'{tab_id}\')">{report["repo_name"][:30]}</button>'
        contents += f'<div id="{tab_id}" class="tabcontent">{report["html_content"]}</div>'
    
    summary_id = "summary"
    tabs = f'<button class="tablinks" onclick="openTab(event, \'{summary_id}\')">Summary</button>' + tabs
    contents = f'<div id="{summary_id}" class="tabcontent">{summary_report}</div>' + contents
    
    html_content = f"""
    <html>
    <head>
        <title>GitHub Repositories Migration Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            h1 {{ color: #333; }}
            h2 {{ color: #666; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #dddddd; text-align: left; padding: 8px; }}
            th {{ background-color: #f2f2f2; }}
            .tab {{ overflow: hidden; border: 1px solid #ccc; background-color: #f1f1f1; }}
            .tab button {{ background-color: inherit; float: left; border: none; outline: none; cursor: pointer; padding: 14px 16px; transition: 0.3s; font-size: 17px; }}
            .tab button:hover {{ background-color: #ddd; }}
            .tab button.active {{ background-color: #ccc; }}
            .tabcontent {{ display: none; padding: 6px 12px; border-top: none; border-left: 1px solid #ccc; border-right: 1px solid #ccc; border-bottom: 1px solid #ccc; }}
        </style>
        <script>
            function openTab(evt, tabName) {{
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tabcontent");
                for (i = 0; i < tabcontent.length; i++) {{
                    tabcontent[i].style.display = "none";
                }}
                tablinks = document.getElementsByClassName("tablinks");
                for (i = 0; i < tablinks.length; i++) {{
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                }}
                document.getElementById(tabName).style.display = "block";
                evt.currentTarget.className += " active";
            }}
            function downloadExcel() {{
                var wb = XLSX.utils.book_new();
                var summary = document.querySelector('#summary table');
                if (summary) {{
                    var summaryWS = XLSX.utils.table_to_sheet(summary);
                    XLSX.utils.book_append_sheet(wb, summaryWS, 'Summary');
                }}
                
                var tabs = document.getElementsByClassName('tabcontent');
                for (var i = 0; i < tabs.length; i++) {{
                    var tabName = tabs[i].id;
                    if (tabName !== 'summary') {{
                        var tabTables = tabs[i].getElementsByTagName('table');
                        var sheetData = [];
                        for (var j = 0; j < tabTables.length; j++) {{
                            var table = tabTables[j];
                            var sheetTitle = table.previousElementSibling ? table.previousElementSibling.innerText : '';
                            sheetData.push([sheetTitle]);
                            var tableData = XLSX.utils.sheet_to_json(XLSX.utils.table_to_sheet(table), {{header:1}});
                            sheetData = sheetData.concat(tableData);
                            sheetData.push([]);  // Add a blank line between tables
                        }}
                        var tabWS = XLSX.utils.aoa_to_sheet(sheetData);
                        var sheetName = sanitizeSheetTitle(tabName);
                        XLSX.utils.book_append_sheet(wb, tabWS, sheetName);
                    }}
                }}
                
                XLSX.writeFile(wb, '{filename.replace('.html', '.xlsx')}');
            }}
            function sanitizeSheetTitle(title) {{
                var invalidChars = /[\\\\/:*?\\[\\]]/g;
                return title.replace(invalidChars, '').substring(0, 31);
            }}
        </script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.15.6/xlsx.full.min.js"></script>
    </head>
    <body>
        <button onclick="downloadExcel()">Download as Excel</button>
        <div class="tab">
            """ + tabs + """
        </div>
        """ + contents + """
        <script>
            document.getElementsByClassName("tablinks")[0].click();
        </script>
    </body>
    </html>
    """
    
    with open(filename, "w", encoding='utf-8') as file:
        file.write(html_content)

def generate_report_for_repo(repo, include_estimates):
    try:
        repo_name = repo.full_name
        print(f"Generating report for repository {repo_name}...")
        repo_info = get_repo_info(repo_name)
        
        print("Counting Java files...")
        java_files_count, java_files_lines = count_files(repo_name, ['.java'])
        
        print("Fetching file details...")
        file_details = get_file_details(repo_name, [])
        
        print("Fetching dependencies and versions...")
        dependencies, java_versions, spring_boot_versions, angular_versions, node_versions, build_tool, group_id, artifact_id, version, name, parent_group_id, parent_artifact_id, parent_version, parent_name = get_dependencies_and_versions(repo_name)
        
        print("Fetching configuration files...")
        config_files = get_files_recursively(repo, '', [".properties", ".yml", ".json"])
        
        print("Fetching deployment manifests...")
        deployment_manifests = get_files_recursively(repo, '', [".yml", ".yaml", "manifest.yml", "Dockerfile"])
        
        print("Analyzing manifest files...")
        manifest_details = analyze_manifest_files(repo_name)
        
        print("Searching for PCF references...")
        pcf_references = search_pcf_references(repo_name)
        
        print("Calculating complexity and estimates...")
        complexity = calculate_complexity(java_files_count, len(dependencies), len(config_files), len(pcf_references))
        
        helios_onboarding = 'Yes' if any(f.path.startswith('helios') or f.path.endswith('helios-config.yml') for f in get_files_recursively(repo)) else 'No'
        
        deployed_to_pcf = 'Yes' if any(f.name.startswith('manifest') and f.name.endswith('.yml') for f in get_files_recursively(repo)) else 'No'
        
        html_content = generate_html_content(
            repo_name, repo_info, java_files_count, java_files_lines, file_details, dependencies, config_files, deployment_manifests, 
            manifest_details, pcf_references, java_versions, spring_boot_versions, angular_versions, node_versions, build_tool, group_id, artifact_id, version, name, parent_group_id, parent_artifact_id, parent_version, parent_name, complexity, include_estimates, helios_onboarding, deployed_to_pcf
        )
        
        report = {
            "repo_name": repo_name,
            "html_content": html_content,
            "file_details": [file_detail for file_detail in file_details if isinstance(file_detail, dict)],  # Ensure serializable
            "java_files_count": java_files_count,
            "java_files_lines": java_files_lines,
            "pcf_references": pcf_references,
            "config_files": [cf.path for cf in config_files],  # Serialize only the paths
            "deployment_manifests": [dm.path for dm in deployment_manifests],  # Serialize only the paths
            "dependencies": dependencies,
            "java_versions": java_versions,
            "spring_boot_versions": spring_boot_versions,
            "angular_versions": angular_versions,
            "node_versions": node_versions,
            "build_tool": build_tool,
            "group_id": group_id,
            "artifact_id": artifact_id,
            "version": version,
            "name": name,
            "parent_group_id": parent_group_id,
            "parent_artifact_id": parent_artifact_id,
            "parent_version": parent_version,
            "parent_name": parent_name,
            "complexity": complexity,
            "helios_onboarding": helios_onboarding,
            "deployed_to_pcf": deployed_to_pcf
        }
        
        return report
    
    except Exception as e:
        error_message = f"Error generating report for repository '{repo.full_name}': {e}"
        print(error_message)
        error_report = {
            "repo_name": repo.full_name,
            "html_content": f"<h2>{error_message}</h2>",
            "file_details": [],
            "java_files_count": 0,
            "java_files_lines": 0,
            "pcf_references": [],
            "config_files": [],
            "deployment_manifests": [],
            "dependencies": [],
            "java_versions": [],
            "spring_boot_versions": [],
            "angular_versions": [],
            "node_versions": [],
            "complexity": "N/A",
            "helios_onboarding": "No",
            "deployed_to_pcf": "No"
        }
        return error_report

def generate_html_content(repo_name, repo_info, java_files_count, java_files_lines, file_details, dependencies, config_files, deployment_manifests, manifest_details, pcf_references, java_versions, spring_boot_versions, angular_versions, node_versions, build_tool, group_id, artifact_id, version, name, parent_group_id, parent_artifact_id, parent_version, parent_name, complexity, include_estimates, helios_onboarding, deployed_to_pcf):
    html_content = f"""
        <h1>Migration Report for {repo_name}</h1>
        <p><strong>Generated on:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Repository Info</h2>
        <table>
            <tr><th>Name</th><td>{repo_info['name']}</td></tr>
            <tr><th>Description</th><td>{repo_info['description']}</td></tr>
            <tr><th>Language</th><td>{repo_info['language']}</td></tr>
            <tr><th>Language Version</th><td>{', '.join(set(java_versions + node_versions))}</td></tr>
            <tr><th>Build</th><td>{build_tool}</td></tr>
            <tr><th>Group ID</th><td>{group_id}</td></tr>
            <tr><th>Artifact ID</th><td>{artifact_id}</td></tr>
            <tr><th>Version</th><td>{version}</td></tr>
            <tr><th>Name</th><td>{name}</td></tr>
            <tr><th>Parent Group ID</th><td>{parent_group_id}</td></tr>
            <tr><th>Parent Artifact ID</th><td>{parent_artifact_id}</td></tr>
            <tr><th>Parent Version</th><td>{parent_version}</td></tr>
            <tr><th>Parent Name</th><td>{parent_name}</td></tr>
            <tr><th>Topics</th><td>{', '.join(repo_info['topics'])}</td></tr>
            <tr><th>Default Branch</th><td>{repo_info['default_branch']}</td></tr>
            <tr><th>Size (bytes)</th><td>{repo_info['size']}</td></tr>
            <tr><th>Created At</th><td>{repo_info['created_at']}</td></tr>
            <tr><th>Updated At</th><td>{repo_info['updated_at']}</td></tr>
            <tr><th>Subscribers Count</th><td>{repo_info['subscribers_count']}</td></tr>
            <tr><th>Stargazers Count</th><td>{repo_info['stargazers_count']}</td></tr>
            <tr><th>Watchers Count</th><td>{repo_info['watchers_count']}</td></tr>
            <tr><th>Forks Count</th><td>{repo_info['forks_count']}</td></tr>
            <tr><th>Open Issues Count</th><td>{repo_info['open_issues_count']}</td></tr>
            <tr><th>License</th><td>{repo_info['license']}</td></tr>
            <tr><th>GitHub URL</th><td><a href="{repo_info['html_url']}">{repo_info['html_url']}</a></td></tr>
        </table>

        <h2>Summary</h2>
        <table>
            <tr><th>Total Files</th><td>{len(file_details)}</td></tr>
            <tr><th>Java Files</th><td>{java_files_count}</td></tr>
            <tr><th>Application Lines of Code</th><td>{java_files_lines}</td></tr>
            <tr><th>PCF References</td><td>{len(pcf_references)}</td></tr>
            <tr><th>Configuration Files</td><td>{len(config_files)}</td></tr>
            <tr><th>Deployment Manifests</td><td>{len(deployment_manifests)}</td></tr>
            <tr><th>Dependencies</td><td>{len(dependencies)}</td></tr>
            <tr><th>Java Versions</th><td>{', '.join(set(java_versions))}</td></tr>
            <tr><th>Spring Boot Versions</th><td>{', '.join(set(spring_boot_versions))}</td></tr>
            <tr><th>Angular Versions</th><td>{', '.join(set(angular_versions))}</td></tr>
            <tr><th>Node Versions</td><td>{', '.join(set(node_versions))}</td></tr>
            <tr><th>Complexity</td><td>{complexity}</td></tr>
            <tr><th>Helios Onboarding</td><td>{helios_onboarding}</td></tr>
            <tr><th>Deployed to PCF</td><td>{deployed_to_pcf}</td></tr>
    """
    
    html_content += """
        </table>
        
    <h2>Dependencies</h2>
        <table>
            <tr><th>Group ID</th><th>Artifact ID</th><th>Version</th></tr>
    """
    for dep in dependencies:
        html_content += f"<tr><td>{dep['group_id']}</td><td>{dep['artifact_id']}</td><td>{dep['version']}</td></tr>"
    
    html_content += """
        </table>
       
        <h2>File Details</h2>
        <table>
            <tr><th>Name</th><th>Path</th><th>Size (bytes)</th><th>Lines of Code</th></tr>
    """
    
    for file_detail in file_details:
        html_content += f"<tr><td>{file_detail['name']}</td><td>{file_detail['path']}</td><td>{file_detail['size']}</td><td>{file_detail['lines_of_code']}</td></tr>"
    
    html_content += """
        </table>
    """
    
    # Add sections for Configuration Files, Deployment Manifests, etc.
    sections = [
        ("Configuration Files", config_files),
        ("Deployment Manifests", deployment_manifests),
    ]
    
    for section_title, files in sections:
        if files:
            html_content += f"""
            <h2>{section_title}</h2>
            <table>
                <tr><th>Name</th><th>Path</th><th>Size (bytes)</th><th>Lines of Code</th></tr>
            """
            for file_path in files:
                file_detail = next((fd for fd in file_details if fd['path'] == file_path), None)
                if file_detail:
                    html_content += f"<tr><td>{file_detail['name']}</td><td>{file_detail['path']}</td><td>{file_detail['size']}</td><td>{file_detail['lines_of_code']}</td></tr>"
            html_content += """
            </table>
            """
    
    # Add Manifest Files Analysis section if not empty
    if manifest_details:
        html_content += """
        <h2>Manifest Files Analysis</h2>
        <table>
            <tr><th>Name</th><th>Path</th><th>Size (bytes)</th><th>Lines of Code</th><th>Content</th></tr>
        """
        for manifest in manifest_details:
            html_content += f"<tr><td>{manifest['name']}</td><td>{manifest['path']}</td><td>{manifest['size']}</td><td>{manifest['lines_of_code']}</td><td><pre>{manifest['content']}</pre></td></tr>"
        html_content += """
        </table>
        """
    
    # Add PCF References section if not empty
    if pcf_references:
        html_content += """
        <h2>PCF References</h2>
        <table>
            <tr><th>Name</th><th>Path</th><th>Size (bytes)</th><th>Lines of Code</th><th>Line Number</th><th>Line Content</th></tr>
        """
        for reference in pcf_references:
            html_content += f"<tr><td>{reference['name']}</td><td>{reference['path']}</td><td>{reference['size']}</td><td>{reference['lines_of_code']}</td><td>{reference['line_number']}</td><td>{reference['line_content']}</td></tr>"
        html_content += """
        </table>
        """
    
    # Add Java Versions section if not empty
    if java_versions:
        html_content += """
        <h2>Java Versions (from build files)</h2>
        <table>
            <tr><th>File</th><th>Java Version</th></tr>
        """
        for version in java_versions:
            html_content += f"<tr><td>build file</td><td>{version}</td></tr>"
        html_content += """
        </table>
        """
    
    # Add Spring Boot Versions section if not empty
    if spring_boot_versions:
        html_content += """
        <h2>Spring Boot Versions</h2>
        <table>
            <tr><th>Version</th></tr>
        """
        for version in spring_boot_versions:
            html_content += f"<tr><td>{version}</td></tr>"
        html_content += """
        </table>
        """
    
    # Add Angular Versions section if not empty
    if angular_versions:
        html_content += """
        <h2>Angular Versions</h2>
        <table>
            <tr><th>Version</th></tr>
        """
        for version in angular_versions:
            html_content += f"<tr><td>{version}</td></tr>"
        html_content += """
        </table>
        """
    
    # Add Node Versions section if not empty
    if node_versions:
        html_content += """
        <h2>Node Versions</h2>
        <table>
            <tr><th>Version</th></tr>
        """
        for version in node_versions:
            html_content += f"<tr><td>{version}</td></tr>"
        html_content += """
        </table>
        """
    
    return html_content

def generate_summary_report(repo_reports):
    summary_content = f"""
        <h1>Overall Summary Report</h1>
        <p><strong>Generated on:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <h2>Summary of Repositories</h2>
        <table>
            <tr>
                <th>Repository Name</th>
                <th>Total Files</th>
                <th>Java Files</th>
                <th>Application Lines of Code</th>
                <th>PCF References</th>
                <th>Configuration Files</th>
                <th>Deployment Manifests</th>
                <th>Dependencies</th>
                <th>Java Versions</th>
                <th>Spring Boot Versions</th>
                <th>Angular Versions</th>
                <th>Node Versions</th>
                <th>Complexity</th>
                <th>Helios Onboarding</th>
                <th>Deployed to PCF</th>
            </tr>
    """
    for report in repo_reports:
        summary_content += f"""
            <tr>
                <td>{report["repo_name"]}</td>
                <td>{len(report["file_details"])}</td>
                <td>{report["java_files_count"]}</td>
                <td>{report["java_files_lines"]}</td>
                <td>{len(report["pcf_references"])}</td>
                <td>{len(report["config_files"])}</td>
                <td>{len(report["deployment_manifests"])}</td>
                <td>{len(report["dependencies"])}</td>
                <td>{', '.join(set(report["java_versions"]))}</td>
                <td>{', '.join(set(report["spring_boot_versions"]))}</td>
                <td>{', '.join(set(report["angular_versions"]))}</td>
                <td>{', '.join(set(report["node_versions"]))}</td>
                <td>{report["complexity"]}</td>
                <td>{report["helios_onboarding"]}</td>
                <td>{report["deployed_to_pcf"]}</td>
            </tr>
        """
    summary_content += "</table>"
    return summary_content

def serialize_repo_reports(repo_reports):
    serialized_reports = []
    for report in repo_reports:
        serialized_report = {k: v for k, v in report.items() if k not in ["file_details", "config_files", "deployment_manifests"]}
        serialized_report["file_details"] = [fd for fd in report["file_details"] if isinstance(fd, dict)]
        serialized_report["config_files"] = [cf for cf in report["config_files"]]
        serialized_report["deployment_manifests"] = [dm for dm in report["deployment_manifests"]]
        serialized_reports.append(serialized_report)
    return serialized_reports

def save_checkpoint(username, repo_reports):
    checkpoint_data = {
        "username": username,
        "repo_reports": serialize_repo_reports(repo_reports)
    }
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint_data, f)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                checkpoint_data = json.load(f)
                return checkpoint_data["username"], checkpoint_data["repo_reports"]
        except json.JSONDecodeError as e:
            print(f"Error loading checkpoint file: {e}")
            return None, []
    return None, []

def delete_checkpoint_file():
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        print(f"Checkpoint file {CHECKPOINT_FILE} deleted.")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate migration report for GitHub repositories.')
    parser.add_argument('repository', help='GitHub repository name (e.g., username/repo) or username to analyze all repositories')
    parser.add_argument('--includeestimates', help='Include Dev and QA effort estimates in the report', choices=['Yes', 'No'], default='No')
    args = parser.parse_args()
    
    repo_name_or_user = args.repository
    include_estimates = args.includeestimates == 'Yes'
    
    try:
        # Load checkpoint
        username, repo_reports = load_checkpoint()
        if username is None:
            username = repo_name_or_user

        if '/' in username:
            # Single repository
            repo_name = username
            print(f"Gathering repository information for {repo_name}...")
            repo = g.get_repo(repo_name)
            report = generate_report_for_repo(repo, include_estimates)
            if report:
                repo_reports.append(report)
        else:
            # User's all repositories
            print(f"Gathering repositories for user {username}...")
            user = g.get_user(username)
            repo_names = [repo.full_name for repo in user.get_repos(type='all')]  # Include both public and private repositories
            
            # Load repo names that have already been processed
            processed_repo_names = {report["repo_name"] for report in repo_reports}
            
            for repo_name in repo_names:
                if repo_name in processed_repo_names:
                    continue  # Skip already processed repositories
                
                repo = g.get_repo(repo_name)
                try:
                    report = generate_report_for_repo(repo, include_estimates)
                    if report:
                        repo_reports.append(report)
                    # Save checkpoint after each repository
                    save_checkpoint(username, repo_reports)
                    # Update HTML report after each repository
                    summary_report = generate_summary_report(repo_reports)
                    html_filename = f"{username.replace('/', '_')}_analysis.html"
                    generate_html_report(repo_reports, summary_report, html_filename)
                except GithubException as e:
                    if e.status == 403:
                        print(f"Access denied for repository {repo.full_name}, skipping...")
                    else:
                        raise e
        
        # Generate overall summary report
        summary_report = generate_summary_report(repo_reports)
        
        # Generate HTML report with tabs
        html_filename = f"{username.replace('/', '_')}_analysis.html" if username else f"{repo_name.replace('/', '_')}_analysis.html"
        generate_html_report(repo_reports, summary_report, html_filename)
        print(f"Report generated: {html_filename}")

        # Delete checkpoint file after successful run
        delete_checkpoint_file()
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
