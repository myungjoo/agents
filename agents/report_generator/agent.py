"""
Report Generator Agent Implementation

Creates comprehensive audit reports from all agent results,
including summaries, recommendations, and detailed findings.
"""

import os
import json
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from agents.base import BaseAgent, AgentType, AgentContext, AgentResult
from common.llm import LLMRequest


class ReportGenerator(BaseAgent):
    """Agent for generating comprehensive audit reports."""
    
    def __init__(self):
        super().__init__(AgentType.REPORT_GENERATOR, "Report Generator")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "name": "Report Generator",
            "description": "Generates comprehensive audit reports from all agent results",
            "capabilities": [
                "Compile results from all agents",
                "Generate executive summary",
                "Create detailed findings report",
                "Generate recommendations",
                "Export to multiple formats (JSON, HTML, PDF)",
                "Include performance metrics and statistics"
            ],
            "outputs": [
                "executive_summary",
                "detailed_findings",
                "recommendations",
                "performance_metrics",
                "export_files"
            ]
        }
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute report generation."""
        try:
            # Compile all agent results
            all_results = self._compile_agent_results(context)
            
            # Generate executive summary
            executive_summary = await self._generate_executive_summary(all_results)
            
            # Create detailed findings
            detailed_findings = await self._create_detailed_findings(all_results)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(all_results)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(all_results)
            
            # Create export files
            export_files = await self._create_export_files(
                context, all_results, executive_summary, 
                detailed_findings, recommendations, performance_metrics
            )
            
            # Compile final report
            report_data = {
                "audit_id": context.audit_id,
                "repository_url": context.repository_url,
                "branch": context.branch,
                "generated_at": datetime.utcnow().isoformat(),
                "executive_summary": executive_summary,
                "detailed_findings": detailed_findings,
                "recommendations": recommendations,
                "performance_metrics": performance_metrics,
                "export_files": export_files,
                "agent_results": all_results
            }
            
            return AgentResult(
                success=True,
                data=report_data,
                metadata={
                    "audit_id": context.audit_id,
                    "repository_url": context.repository_url,
                    "report_files": list(export_files.keys())
                }
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                metadata={
                    "audit_id": context.audit_id,
                    "repository_url": context.repository_url
                }
            )
    
    def _compile_agent_results(self, context: AgentContext) -> Dict[str, Any]:
        """Compile results from all agents."""
        compiled_results = {}
        
        for agent_name, result in context.agent_results.items():
            if result.success:
                compiled_results[agent_name] = result.data
            else:
                compiled_results[agent_name] = {
                    "error": result.error,
                    "status": "failed"
                }
        
        return compiled_results
    
    async def _generate_executive_summary(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary using LLM."""
        # Prepare context for LLM
        context_data = self._prepare_summary_context(all_results)
        
        prompt = f"""
        Create an executive summary for a code audit report based on the following findings:

        Repository Analysis: {context_data.get('repository_analysis', 'N/A')}
        Issues Found: {context_data.get('issues_summary', 'N/A')}
        Fixes Applied: {context_data.get('fixes_summary', 'N/A')}
        Test Results: {context_data.get('test_results', 'N/A')}

        Please provide:
        1. Overall assessment (1-2 sentences)
        2. Key findings (3-5 bullet points)
        3. Critical issues that need immediate attention
        4. Estimated effort for addressing issues
        5. Risk assessment

        Format the response as a structured summary.
        """
        
        request = LLMRequest(
            prompt=prompt,
            system_message="You are an expert software auditor creating executive summaries for technical stakeholders.",
            temperature=0.1,
            max_tokens=1000
        )
        
        response = await self.call_llm(request)
        
        if response.error:
            return {
                "summary": "Failed to generate executive summary",
                "error": response.error
            }
        
        return {
            "summary": response.content,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def _create_detailed_findings(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed findings report."""
        findings = {
            "repository_analysis": all_results.get('repository_analyzer', {}),
            "issues": all_results.get('issue_detector', {}),
            "fixes": all_results.get('code_fixer', {}),
            "tests": all_results.get('test_runner', {}),
            "metadata": {
                "total_issues": 0,
                "critical_issues": 0,
                "warnings": 0,
                "fixes_applied": 0,
                "tests_passed": 0,
                "tests_failed": 0
            }
        }
        
        # Calculate statistics
        if 'issue_detector' in all_results:
            issues_data = all_results['issue_detector']
            if isinstance(issues_data, dict):
                findings['metadata']['total_issues'] = len(issues_data.get('issues', []))
                findings['metadata']['critical_issues'] = len([
                    i for i in issues_data.get('issues', [])
                    if i.get('severity') == 'critical'
                ])
                findings['metadata']['warnings'] = len([
                    i for i in issues_data.get('issues', [])
                    if i.get('severity') == 'warning'
                ])
        
        if 'code_fixer' in all_results:
            fixes_data = all_results['code_fixer']
            if isinstance(fixes_data, dict):
                findings['metadata']['fixes_applied'] = len(fixes_data.get('fixes', []))
        
        if 'test_runner' in all_results:
            tests_data = all_results['test_runner']
            if isinstance(tests_data, dict):
                findings['metadata']['tests_passed'] = tests_data.get('passed_tests', 0)
                findings['metadata']['tests_failed'] = tests_data.get('failed_tests', 0)
        
        return findings
    
    async def _generate_recommendations(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations using LLM."""
        context_data = self._prepare_recommendations_context(all_results)
        
        prompt = f"""
        Based on the following code audit findings, provide actionable recommendations:

        Issues Found: {context_data.get('issues_summary', 'N/A')}
        Current State: {context_data.get('current_state', 'N/A')}
        Test Results: {context_data.get('test_results', 'N/A')}

        Please provide:
        1. Immediate actions (high priority)
        2. Short-term improvements (medium priority)
        3. Long-term recommendations (low priority)
        4. Security considerations
        5. Performance optimizations
        6. Code quality improvements

        Format as structured recommendations with priority levels.
        """
        
        request = LLMRequest(
            prompt=prompt,
            system_message="You are an expert software architect providing actionable recommendations for code improvements.",
            temperature=0.1,
            max_tokens=1500
        )
        
        response = await self.call_llm(request)
        
        if response.error:
            return {
                "recommendations": "Failed to generate recommendations",
                "error": response.error
            }
        
        return {
            "recommendations": response.content,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_performance_metrics(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics from all agent results."""
        metrics = {
            "total_execution_time": 0.0,
            "agent_performance": {},
            "llm_usage": {
                "total_calls": 0,
                "total_tokens": 0,
                "average_response_time": 0.0
            },
            "memory_usage": {
                "peak_memory": 0.0,
                "average_memory": 0.0
            }
        }
        
        # Calculate metrics from agent results
        for agent_name, result in all_results.items():
            if isinstance(result, dict) and 'metadata' in result:
                metadata = result['metadata']
                
                # Execution time
                exec_time = metadata.get('execution_time', 0.0)
                metrics['total_execution_time'] += exec_time
                metrics['agent_performance'][agent_name] = {
                    'execution_time': exec_time,
                    'status': 'completed' if result.get('success', False) else 'failed'
                }
                
                # LLM usage
                llm_calls = metadata.get('llm_calls', 0)
                metrics['llm_usage']['total_calls'] += llm_calls
                
                # Memory usage
                memory = metadata.get('memory_usage', 0.0)
                if memory > metrics['memory_usage']['peak_memory']:
                    metrics['memory_usage']['peak_memory'] = memory
        
        # Calculate averages
        if metrics['llm_usage']['total_calls'] > 0:
            metrics['llm_usage']['average_response_time'] = (
                metrics['total_execution_time'] / metrics['llm_usage']['total_calls']
            )
        
        return metrics
    
    async def _create_export_files(
        self, context: AgentContext, all_results: Dict[str, Any],
        executive_summary: Dict[str, Any], detailed_findings: Dict[str, Any],
        recommendations: Dict[str, Any], performance_metrics: Dict[str, Any]
    ) -> Dict[str, str]:
        """Create export files in various formats."""
        export_files = {}
        
        # Create reports directory
        reports_dir = os.path.join(context.working_directory, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # JSON export
        json_report = {
            "audit_id": context.audit_id,
            "repository_url": context.repository_url,
            "branch": context.branch,
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": executive_summary,
            "detailed_findings": detailed_findings,
            "recommendations": recommendations,
            "performance_metrics": performance_metrics,
            "agent_results": all_results
        }
        
        json_file = os.path.join(reports_dir, f"audit_report_{context.audit_id}.json")
        with open(json_file, 'w') as f:
            json.dump(json_report, f, indent=2, default=str)
        export_files['json'] = json_file
        
        # YAML export
        yaml_file = os.path.join(reports_dir, f"audit_report_{context.audit_id}.yaml")
        with open(yaml_file, 'w') as f:
            yaml.dump(json_report, f, default_flow_style=False, default_style='')
        export_files['yaml'] = yaml_file
        
        # HTML export
        html_content = await self._generate_html_report(
            context, executive_summary, detailed_findings, 
            recommendations, performance_metrics
        )
        html_file = os.path.join(reports_dir, f"audit_report_{context.audit_id}.html")
        with open(html_file, 'w') as f:
            f.write(html_content)
        export_files['html'] = html_file
        
        return export_files
    
    async def _generate_html_report(
        self, context: AgentContext, executive_summary: Dict[str, Any],
        detailed_findings: Dict[str, Any], recommendations: Dict[str, Any],
        performance_metrics: Dict[str, Any]
    ) -> str:
        """Generate HTML report."""
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Audit Report - {context.repository_url}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e9ecef; border-radius: 3px; }}
        .critical {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .success {{ color: #28a745; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Code Audit Report</h1>
        <p><strong>Repository:</strong> {context.repository_url}</p>
        <p><strong>Branch:</strong> {context.branch}</p>
        <p><strong>Audit ID:</strong> {context.audit_id}</p>
        <p><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
    
    <div class="section">
        <h2>Executive Summary</h2>
        <div>{executive_summary.get('summary', 'No summary available')}</div>
    </div>
    
    <div class="section">
        <h2>Key Metrics</h2>
        <div class="metric">
            <strong>Total Issues:</strong> {detailed_findings.get('metadata', {}).get('total_issues', 0)}
        </div>
        <div class="metric">
            <strong>Critical Issues:</strong> {detailed_findings.get('metadata', {}).get('critical_issues', 0)}
        </div>
        <div class="metric">
            <strong>Fixes Applied:</strong> {detailed_findings.get('metadata', {}).get('fixes_applied', 0)}
        </div>
        <div class="metric">
            <strong>Tests Passed:</strong> {detailed_findings.get('metadata', {}).get('tests_passed', 0)}
        </div>
    </div>
    
    <div class="section">
        <h2>Recommendations</h2>
        <div>{recommendations.get('recommendations', 'No recommendations available')}</div>
    </div>
    
    <div class="section">
        <h2>Performance Metrics</h2>
        <p><strong>Total Execution Time:</strong> {performance_metrics.get('total_execution_time', 0):.2f} seconds</p>
        <p><strong>LLM Calls:</strong> {performance_metrics.get('llm_usage', {}).get('total_calls', 0)}</p>
        <p><strong>Peak Memory Usage:</strong> {performance_metrics.get('memory_usage', {}).get('peak_memory', 0):.2f} MB</p>
    </div>
</body>
</html>
        """
        
        return html_template
    
    def _prepare_summary_context(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context data for summary generation."""
        context = {}
        
        # Repository analysis summary
        if 'repository_analyzer' in all_results:
            repo_data = all_results['repository_analyzer']
            if isinstance(repo_data, dict):
                context['repository_analysis'] = f"Languages: {', '.join(repo_data.get('languages', {}).get('detected', []))}, Build System: {repo_data.get('build_system', {}).get('type', 'unknown')}"
        
        # Issues summary
        if 'issue_detector' in all_results:
            issues_data = all_results['issue_detector']
            if isinstance(issues_data, dict):
                issues = issues_data.get('issues', [])
                context['issues_summary'] = f"Found {len(issues)} issues ({len([i for i in issues if i.get('severity') == 'critical'])} critical)"
        
        # Fixes summary
        if 'code_fixer' in all_results:
            fixes_data = all_results['code_fixer']
            if isinstance(fixes_data, dict):
                fixes = fixes_data.get('fixes', [])
                context['fixes_summary'] = f"Applied {len(fixes)} fixes"
        
        # Test results
        if 'test_runner' in all_results:
            tests_data = all_results['test_runner']
            if isinstance(tests_data, dict):
                passed = tests_data.get('passed_tests', 0)
                failed = tests_data.get('failed_tests', 0)
                context['test_results'] = f"Tests: {passed} passed, {failed} failed"
        
        return context
    
    def _prepare_recommendations_context(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context data for recommendations generation."""
        context = {}
        
        # Issues summary
        if 'issue_detector' in all_results:
            issues_data = all_results['issue_detector']
            if isinstance(issues_data, dict):
                issues = issues_data.get('issues', [])
                critical = len([i for i in issues if i.get('severity') == 'critical'])
                warnings = len([i for i in issues if i.get('severity') == 'warning'])
                context['issues_summary'] = f"{len(issues)} total issues ({critical} critical, {warnings} warnings)"
        
        # Current state
        if 'repository_analyzer' in all_results:
            repo_data = all_results['repository_analyzer']
            if isinstance(repo_data, dict):
                languages = repo_data.get('languages', {}).get('detected', [])
                build_system = repo_data.get('build_system', {}).get('type', 'unknown')
                context['current_state'] = f"Languages: {', '.join(languages)}, Build: {build_system}"
        
        # Test results
        if 'test_runner' in all_results:
            tests_data = all_results['test_runner']
            if isinstance(tests_data, dict):
                passed = tests_data.get('passed_tests', 0)
                failed = tests_data.get('failed_tests', 0)
                total = passed + failed
                success_rate = (passed / total * 100) if total > 0 else 0
                context['test_results'] = f"Test success rate: {success_rate:.1f}% ({passed}/{total})"
        
        return context