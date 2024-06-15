import os
import argparse
from github import Github, GithubException
from datetime import datetime
import time
import xml.etree.ElementTree as ET

# Set up GitHub API access
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # Ensure this is set as an environment variable
if not GITHUB_TOKEN:
    raise ValueError("Please set your GITHUB_TOKEN environment variable.")
g = Github(GITHUB_TOKEN)

def check_rate_limit():
    rate_limit = g.get_rate_limit()
    core_limit = rate_limit.core
    reset_time = core_limit.reset.timestamp()  # Convert to timestamp
    remaining = core_limit.remaining
    print(f"Rate limit remaining: {remaining}")
    print(f"Reset time: {datetime.fromtimestamp(reset_time)}")
    return remaining, reset_time

def wait_for_rate_limit_reset():
    remaining, reset_time = check_rate_limit()
    if remaining == 0:
        wait_time = max(reset_time - time.time(), 0) + 10  # Add a buffer time
        print(f"Rate limit exceeded. Waiting for {wait_time} seconds before retrying...")
        time.sleep(wait_time)

def get_repo_info(repo_name):
    wait_for_rate_limit_reset()
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
            return get_repo_info(repo_name)
        else:
            raise ValueError(f"Error fetching repository '{repo_name}': {e}")

def get_files_recursively(repo, path='', extensions=None):
    if extensions is None:
        extensions = []
    result_files = []
    contents = repo.get_contents(path)
    for content in contents:
        if content.type == 'dir':
            result_files.extend(get_files_recursively(repo, content.path, extensions))
        else:
            if any(content.name.endswith(ext) for ext in extensions):
                result_files.append(content)
            elif not extensions:  # Add all files if no extensions are specified
                result_files.append(content)
    return result_files

def count_java_files(repo_name):
    wait_for_rate_limit_reset()
    try:
        repo = g.get_repo(repo_name)
        java_files = get_files_recursively(repo, '', ['.java'])
        return len(java_files)
    except GithubException as e:
        if e.status == 403 and 'rate limit exceeded' in str(e):
            wait_for_rate_limit_reset()
            return count_java_files(repo_name)
        else:
            raise ValueError(f"Error counting Java files in repository '{repo_name}': {e}")

def get_file_details(repo_name, extensions):
    wait_for_rate_limit_reset()
    try:
        repo = g.get_repo(repo_name)
        files = get_files_recursively(repo, '', extensions)
        file_details = []
        for file in files:
            content = file.decoded_content.decode('utf-8', errors='ignore')
            lines = content.count('\n') if content else 0
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
            return get_file_details(repo_name, extensions)
        else:
            raise ValueError(f"Error fetching file details from repository '{repo_name}': {e}")

def parse_pom_xml(content):
    root = ET.fromstring(content)
    namespaces = {'maven': 'http://maven.apache.org/POM/4.0.0'}
    dependencies = []
    java_version = 'N/A'
    for dependency in root.findall('.//maven:dependency', namespaces):
        group_id_element = dependency.find('maven:groupId', namespaces)
        artifact_id_element = dependency.find('maven:artifactId', namespaces)
        version_element = dependency.find('maven:version', namespaces)
        
        group_id = group_id_element.text if group_id_element is not None else 'N/A'
        artifact_id = artifact_id_element.text if artifact_id_element is not None else 'N/A'
        version = version_element.text if version_element is not None else 'N/A'
        
        dependencies.append({
            'group_id': group_id,
            'artifact_id': artifact_id,
            'version': version
        })

    # Extract Java version
    java_version_element = root.find('.//maven:properties/maven:java.version', namespaces)
    if java_version_element is not None:
        java_version = java_version_element.text

    return dependencies, java_version

def parse_gradle_file(content):
    java_version = 'N/A'
    lines = content.split('\n')
    for line in lines:
        if 'sourceCompatibility' in line or 'targetCompatibility' in line:
            parts = line.split()
            if len(parts) == 2:
                java_version = parts[1].replace("'", "").replace("\"", "")
    return java_version

def get_dependencies_and_versions(repo_name):
    wait_for_rate_limit_reset()
    try:
        repo = g.get_repo(repo_name)
        pom_files = get_files_recursively(repo, '', ['pom.xml'])
        gradle_files = get_files_recursively(repo, '', ['build.gradle'])
        dependencies = []
        java_versions = []
        for pom_file in pom_files:
            content = repo.get_contents(pom_file.path).decoded_content.decode('utf-8')
            deps, java_version = parse_pom_xml(content)
            dependencies.extend(deps)
            if java_version != 'N/A':
                java_versions.append(java_version)
        for gradle_file in gradle_files:
            content = repo.get_contents(gradle_file.path).decoded_content.decode('utf-8')
            java_version = parse_gradle_file(content)
            if java_version != 'N/A':
                java_versions.append(java_version)
        return dependencies, java_versions
    except GithubException as e:
        if e.status == 403 and 'rate limit exceeded' in str(e):
            wait_for_rate_limit_reset()
            return get_dependencies_and_versions(repo_name)
        else:
            raise ValueError(f"Error fetching dependencies from repository '{repo_name}': {e}")

def analyze_manifest_files(repo_name):
    wait_for_rate_limit_reset()
    try:
        repo = g.get_repo(repo_name)
        manifest_files = get_files_recursively(repo, '', ['manifest.yml'])
        manifest_details = []
        for manifest_file in manifest_files:
            content = repo.get_contents(manifest_file.path).decoded_content.decode('utf-8', errors='ignore')
            lines = content.count('\n') if content else 0
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
            return analyze_manifest_files(repo_name)
        else:
            raise ValueError(f"Error fetching manifest files from repository '{repo_name}': {e}")

def search_pcf_references(repo_name):
    wait_for_rate_limit_reset()
    try:
        repo = g.get_repo(repo_name)
        files = get_files_recursively(repo, '')  # Fetch all files
        pcf_references = []
        for file in files:
            content = repo.get_contents(file.path).decoded_content.decode('utf-8', errors='ignore').lower()
            lines = content.split('\n')
            for line_number, line in enumerate(lines, start=1):
                if 'pcf' in line or 'cloudfoundry' in line:
                    print(f"Found PCF reference in file: {file.path}, line: {line_number}")  # Debug log
                    pcf_references.append({
                        'name': file.name,
                        'path': file.path,
                        'size': file.size,
                        'lines_of_code': content.count('\n'),
                        'line_number': line_number,
                        'line_content': line.strip()
                    })
        return pcf_references
    except GithubException as e:
        if e.status == 403 and 'rate limit exceeded' in str(e):
            wait_for_rate_limit_reset()
            return search_pcf_references(repo_name)
        else:
            raise ValueError(f"Error searching PCF references in repository '{repo_name}': {e}")

def get_pcf_migration_recommendations(pcf_references):
    recommendations = []
    for reference in pcf_references:
        recommendations.append({
            'path': reference['path'],
            'line_number': reference['line_number'],
            'line_content': reference['line_content'],
            'recommendation': f"Replace '{reference['line_content']}' with OCP-specific configuration."
        })
    return recommendations

def calculate_complexity(java_files_count, dependencies_count, config_files_count, pcf_references_count):
    complexity_score = java_files_count + dependencies_count + config_files_count + pcf_references_count
    
    if complexity_score <= 10:
        return "Low"
    elif complexity_score <= 20:
        return "Medium"
    else:
        return "High"

def estimate_migration_time(complexity):
    if complexity == "Low":
        dev_days = 5
        qa_days = 3
    elif complexity == "Medium":
        dev_days = 10
        qa_days = 5
    else:
        dev_days = 20
        qa_days = 10
    return dev_days, qa_days

def generate_html_report(repo_name, repo_info, java_files_count, file_details, dependencies, config_files, deployment_manifests, security_settings, volume_mounts, logging_monitoring, ci_cd_pipelines, scaling_policies, compliance_requirements, documentation, manifest_details, pcf_references, java_versions, pcf_recommendations, complexity, dev_days, qa_days):
    html_content = f"""
    <html>
    <head>
        <title>GitHub Repository Migration Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            h1 {{ color: #333; }}
            h2 {{ color: #666; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #dddddd; text-align: left; padding: 8px; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Migration Report for {repo_name}</h1>
        <p><strong>Generated on:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Repository Info</h2>
        <table>
            <tr><th>Name</th><td>{repo_info['name']}</td></tr>
            <tr><th>Description</th><td>{repo_info['description']}</td></tr>
            <tr><th>Language</th><td>{repo_info['language']}</td></tr>
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
            <tr><th>PCF References</th><td>{len(pcf_references)}</td></tr>
            <tr><th>Configuration Files</th><td>{len(config_files)}</td></tr>
            <tr><th>Deployment Manifests</th><td>{len(deployment_manifests)}</td></tr>
            <tr><th>Dependencies</th><td>{len(dependencies)}</td></tr>
            <tr><th>Java Versions</th><td>{', '.join(set(java_versions))}</td></tr>
            <tr><th>Complexity</th><td>{complexity}</td></tr>
            <tr><th>Development Estimate (days)</th><td>{dev_days}</td></tr>
            <tr><th>QA Estimate (days)</th><td>{qa_days}</td></tr>
        </table>
        
        <h2>Java Files</h2>
        <p>Number of Java files: {java_files_count}</p>
        
        <h2>File Details</h2>
        <table>
            <tr><th>Name</th><th>Path</th><th>Size (bytes)</th><th>Lines of Code</th></tr>
    """
    
    for file_detail in file_details:
        html_content += f"<tr><td>{file_detail['name']}</td><td>{file_detail['path']}</td><td>{file_detail['size']}</td><td>{file_detail['lines_of_code']}</td></tr>"
    
    html_content += """
        </table>
    """
    
    # Add dependencies section if not empty
    if dependencies:
        html_content += """
        <h2>Dependencies</h2>
        <table>
            <tr><th>Group ID</th><th>Artifact ID</th><th>Version</th></tr>
        """
        for dep in dependencies:
            html_content += f"<tr><td>{dep['group_id']}</td><td>{dep['artifact_id']}</td><td>{dep['version']}</td></tr>"
        html_content += """
        </table>
        """

    # Add sections for Configuration Files, Deployment Manifests, etc.
    sections = [
        ("Configuration Files", config_files),
        ("Deployment Manifests", deployment_manifests),
        ("Security Settings", security_settings),
        ("Volume Mounts", volume_mounts),
        ("Logging and Monitoring", logging_monitoring),
        ("CI/CD Pipelines", ci_cd_pipelines),
        ("Scaling Policies", scaling_policies),
        ("Compliance Requirements", compliance_requirements),
        ("Documentation", documentation),
    ]
    
    for section_title, files in sections:
        if files:
            html_content += f"""
            <h2>{section_title}</h2>
            <table>
                <tr><th>Name</th><th>Path</th><th>Size (bytes)</th><th>Lines of Code</th></tr>
            """
            for file in files:
                file_content = next((fd for fd in file_details if fd['path'] == file.path), None)
                if file_content:
                    html_content += f"<tr><td>{file_content['name']}</td><td>{file_content['path']}</td><td>{file_content['size']}</td><td>{file_content['lines_of_code']}</td></tr>"
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

    # Add PCF Migration Recommendations section if not empty
    if pcf_recommendations:
        html_content += """
        <h2>PCF Migration Recommendations</h2>
        <table>
            <tr><th>Path</th><th>Line Number</th><th>Line Content</th><th>Recommendation</th></tr>
        """
        for recommendation in pcf_recommendations:
            html_content += f"<tr><td>{recommendation['path']}</td><td>{recommendation['line_number']}</td><td>{recommendation['line_content']}</td><td>{recommendation['recommendation']}</td></tr>"
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
    
    html_content += """
    </body>
    </html>
    """
    
    with open("migration_report.html", "w", encoding='utf-8') as file:
        file.write(html_content)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate migration report for a GitHub repository.')
    parser.add_argument('repository', help='GitHub repository name (e.g., username/repo)')
    args = parser.parse_args()
    
    repo_name = args.repository
    
    try:
        print(f"Gathering repository information for {repo_name}...")
        repo_info = get_repo_info(repo_name)
        
        repo = g.get_repo(repo_name)
        
        print("Counting Java files...")
        java_files_count = count_java_files(repo_name)
        
        print("Fetching file details...")
        file_details = get_file_details(repo_name, [".java", ".properties", ".yml", ".yaml", "manifest.yml", "Dockerfile"])
        
        print("Fetching dependencies and Java versions...")
        dependencies, java_versions = get_dependencies_and_versions(repo_name)
        
        print("Fetching configuration files...")
        config_files = get_files_recursively(repo, '', [".properties", ".yml", ".json"])
        
        print("Fetching deployment manifests...")
        deployment_manifests = get_files_recursively(repo, '', [".yml", ".yaml", "manifest.yml", "Dockerfile"])
        
        print("Fetching security settings...")
        security_settings = get_files_recursively(repo, '', [".yml"])
        
        print("Fetching volume mounts...")
        volume_mounts = get_files_recursively(repo, '', [".yml"])
        
        print("Fetching logging and monitoring configurations...")
        logging_monitoring = get_files_recursively(repo, '', [".yml"])
        
        print("Fetching CI/CD pipelines...")
        ci_cd_pipelines = get_files_recursively(repo, '', [".gitlab-ci.yml", "Jenkinsfile"])
        
        print("Fetching scaling policies...")
        scaling_policies = get_files_recursively(repo, '', [".yml"])
        
        print("Fetching compliance requirements...")
        compliance_requirements = get_files_recursively(repo, '', [".yml"])
        
        print("Fetching documentation...")
        documentation = get_files_recursively(repo, '', [".md"])
        
        print("Analyzing manifest files...")
        manifest_details = analyze_manifest_files(repo_name)
        
        print("Searching for PCF references...")
        pcf_references = search_pcf_references(repo_name)
        
        print("Generating PCF migration recommendations...")
        pcf_recommendations = get_pcf_migration_recommendations(pcf_references)
        
        print("Calculating complexity and estimates...")
        complexity = calculate_complexity(java_files_count, len(dependencies), len(config_files), len(pcf_references))
        dev_days, qa_days = estimate_migration_time(complexity)
        
        print("Generating HTML report...")
        generate_html_report(
            repo_name, repo_info, java_files_count, file_details, dependencies, config_files, deployment_manifests, 
            security_settings, volume_mounts, logging_monitoring, ci_cd_pipelines, 
            scaling_policies, compliance_requirements, documentation, manifest_details, pcf_references, java_versions, pcf_recommendations, complexity, dev_days, qa_days
        )
        print("Report generated: migration_report.html")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
