#!/usr/bin/env python3
"""
Dynamic Generation LLM Monitor test data generation tool

Generates mock data needed by the tests, to ease debugging and development
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


class TestDataGenerator:
    """Test data generator"""
    
    def __init__(self):
        self.base_time = datetime.now() - timedelta(hours=2)
        self.generation_counter = 10000
        self.node_counter = 1000
        self.branch_counter = 50000
        
        # Predefined test scenarios
        self.scenarios = [
            "Data cleaning and preprocessing",
            "Machine learning model training",
            "Data visualization and analysis",
            "Text processing and analysis",
            "Image processing pipeline",
            "Real-time data monitoring",
            "ETL data pipeline",
            "API development"
        ]
        
        self.programming_languages = ["Python", "R", "SQL", "JavaScript"]
        self.node_types = ["Data input", "Data processing", "Algorithm computation", "Result output", "Intermediate transformation"]
        self.error_types = [
            "Parameter type error", "Data format mismatch", "Out of memory", 
            "Computation timeout", "Missing dependency package", "Permission error"
        ]

    def generate_dynamic_generation(self, generation_id: int = None) -> Dict[str, Any]:
        """Generate dynamic_generation test data"""
        if generation_id is None:
            generation_id = self.generation_counter
            self.generation_counter += 1
            
        scenario = random.choice(self.scenarios)
        
        return {
            "generation_id": generation_id,
            "analysis_id": random.randint(1, 100),
            "previous_node_id": self.node_counter,
            "previous_computation_id": random.randint(1000, 9999),
            "max_node": random.randint(3, 15),
            "max_branch": random.randint(1, 5),
            "user_request": f"Please create a {scenario} workflow for me",
            "created_time": self.base_time,
            "state": random.choice(["running", "completed", "stopped", "failed"]),
            "rest_node_count": random.randint(0, 10),
            "computation_resource_configure": json.dumps({
                "ram": random.choice([1024, 2048, 4096, 8192]),
                "vcpu": random.choice([1, 2, 4, 8]),
                "timeout": random.choice([300, 600, 1800, 3600]),
                "gpu": random.choice([0, 1])
            }),
            "generation_mode": random.choice(["mixed", "code_only", "existing_only"]),
            "max_debug": random.randint(3, 10),
            "llm_model": random.choice(["gpt-4", "gpt-3.5-turbo", "claude-3"])
        }

    def generate_branch(self, generation_id: int, end_node_id: int = None) -> Dict[str, Any]:
        """Generate branch test data"""
        branch_id = self.branch_counter
        self.branch_counter += 1
        
        if end_node_id is None:
            end_node_id = self.node_counter + random.randint(1, 5)
            
        created_time = self.base_time + timedelta(minutes=random.randint(1, 30))
        updated_time = created_time + timedelta(minutes=random.randint(5, 60))
        
        return {
            "id": branch_id,
            "dynamic_generation_id": generation_id,
            "end_node_id": end_node_id,
            "state": random.choice(["running", "done", "failed"]),
            "created_time": created_time,
            "updated_time": updated_time
        }

    def generate_nodes(self, generation_id: int, count: int = 4) -> List[Dict[str, Any]]:
        """Generate node test data"""
        nodes = []
        current_time = self.base_time
        
        for i in range(count):
            node_id = self.node_counter + i
            node_type = random.choice(self.node_types)
            
            current_time += timedelta(minutes=random.randint(2, 10))
            
            node = {
                "id": node_id,
                "name": f"{node_type} node_{i+1}",
                "analysis_id": random.randint(1, 100),
                "type": "computation",
                "state": random.choice(["original", "running", "finished", "failed"]),
                "created_time": current_time,
                "updated_time": current_time + timedelta(minutes=1),
                "dynamic_generation_id": generation_id,
                "function_block_id": random.randint(100, 999),
                "function_block_version_id": random.randint(1000, 9999),
                "computation_params": json.dumps({
                    "param1": random.choice(["value1", "value2", "value3"]),
                    "param2": random.randint(1, 100),
                    "param3": random.random()
                })
            }
            nodes.append(node)
        
        self.node_counter += count
        return nodes

    def generate_s3_prompt_data(self, scenario: str = None) -> Dict[str, Any]:
        """Generate S3 prompt data"""
        if scenario is None:
            scenario = random.choice(self.scenarios)
            
        return {
            "user_request": f"Generate function blocks related to {scenario}",
            "context": {
                "previous_node_output": {
                    "data_type": random.choice(["CSV", "JSON", "Parquet", "XML"]),
                    "row_count": random.randint(100, 10000),
                    "columns": [f"column_{i}" for i in range(random.randint(3, 10))],
                    "data_quality": {
                        "null_percentage": round(random.random() * 0.1, 3),
                        "duplicate_count": random.randint(0, 100)
                    }
                },
                "user_requirements": [
                    "Ensure data quality", "Improve processing efficiency", "Add error handling", 
                    "Support parallel processing", "Log processing steps"
                ][:random.randint(2, 5)],
                "performance_requirements": {
                    "max_processing_time": random.choice([60, 300, 600, 1800]),
                    "memory_limit": random.choice([512, 1024, 2048, 4096])
                }
            },
            "generation_mode": random.choice(["mixed", "code_only", "existing_only"]),
            "max_branch": random.randint(1, 5),
            "timestamp": int((datetime.now() - timedelta(minutes=random.randint(5, 30))).timestamp() * 1000)
        }

    def generate_s3_output_data(self, programming_language: str = None) -> Dict[str, Any]:
        """Generate S3 output data"""
        if programming_language is None:
            programming_language = random.choice(self.programming_languages)
            
        satisfied = random.choice([True, False])
        
        if satisfied:
            return {
                "satisfied": True,
                "reasoning": "The user's requirement is already satisfied by existing nodes",
                "next_level_function_blocks": [],
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        
        # Generate new function blocks
        function_blocks = []
        for i in range(random.randint(1, 3)):
            fb_name = f"Processing function block_{i+1}"
            
            if programming_language == "Python":
                code = f'''
def process_data_{i+1}(data, **kwargs):
    """
    Main processing logic of {fb_name}
    """
    import pandas as pd
    import numpy as np
    
    # Data processing logic
    processed_data = data.copy()
    
    # Add processing steps
    if 'threshold' in kwargs:
        processed_data = processed_data[processed_data.value > kwargs['threshold']]
    
    return processed_data
'''
            elif programming_language == "R":
                code = f'''
process_data_{i+1} <- function(data, ...) {{
    # Main processing logic of {fb_name}
    library(dplyr)
    
    processed_data <- data %>%
        filter(!is.na(.)) %>%
        mutate(processed = TRUE)
    
    return(processed_data)
}}
'''
            else:
                code = f"// {fb_name}\nfunction processData{i+1}(data) {{ return data; }}"
            
            fb = {
                "name": fb_name,
                "programming_language": programming_language,
                "function_block_code": code.strip(),
                "parameters": json.dumps({
                    "input_data": "{{previous_node_output}}",
                    "threshold": random.random(),
                    "method": random.choice(["default", "advanced", "fast"])
                }),
                "static_config_file_content": {
                    "description": f"{fb_name}: provides data processing capability",
                    "args": [
                        {
                            "name": "threshold",
                            "value_type": "float",
                            "description": "Filter threshold",
                            "default_value": 0.5,
                            "render_type": "number-input"
                        },
                        {
                            "name": "method", 
                            "value_type": "str",
                            "description": "Processing method",
                            "default_value": "default",
                            "render_type": "select",
                            "options": ["default", "advanced", "fast"]
                        }
                    ]
                },
                "requirements_file_content": self._generate_requirements(programming_language)
            }
            function_blocks.append(fb)
        
        return {
            "satisfied": False,
            "reasoning": f"{len(function_blocks)} new function block(s) need to be generated to satisfy the user requirement",
            "next_level_function_blocks": function_blocks,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }

    def generate_retry_session_data(self, node_id: int, computation_id: int) -> Dict[str, Any]:
        """Generate retry session data"""
        error_type = random.choice(self.error_types)
        
        return {
            "node_computation_information": {
                "node_id": node_id,
                "computation_id": computation_id,
                "error_type": error_type.replace(" ", "_").lower(),
                "error_description": f"{error_type} occurred during computation",
                "failed_step": random.choice(["initialization", "data_loading", "processing", "output"]),
                "error_details": {
                    "line_number": random.randint(10, 100),
                    "function_name": f"process_step_{random.randint(1, 5)}",
                    "error_code": f"E{random.randint(1000, 9999)}"
                }
            },
            "input_prompt": f"Please help fix the following error: {error_type}. The error occurred during computation; the relevant parameters or code need to be adjusted.",
            "parameters_fix_solution": {
                "fix_applied": random.choice([True, False]),
                "original_params": {
                    "param1": "original_value",
                    "param2": random.randint(1, 10)
                },
                "fixed_params": {
                    "param1": "fixed_value", 
                    "param2": random.randint(10, 20)
                },
                "fix_explanation": f"Adjusted the relevant parameter settings to address {error_type}"
            },
            "code_fix_solution": {
                "fix_applied": random.choice([True, False]),
                "original_code_snippet": "original_function() { /* original code */ }",
                "fixed_code_snippet": "fixed_function() { /* improved code with error handling */ }",
                "fix_explanation": "Added error handling and parameter validation logic"
            } if random.choice([True, False]) else None,
            "result": {
                "success": random.choice([True, False]),
                "message": "Fix succeeded, restarting computation" if random.choice([True, False]) else "Fix attempt failed, manual intervention required",
                "retry_computation_id": computation_id + 1 if random.choice([True, False]) else None,
                "fix_duration_seconds": random.randint(30, 300)
            }
        }

    def _generate_requirements(self, programming_language: str) -> str:
        """Generate requirements file content"""
        if programming_language == "Python":
            packages = ["pandas>=1.3.0", "numpy>=1.21.0", "scikit-learn>=1.0.0"]
            return "\n".join(random.sample(packages, random.randint(1, len(packages))))
        elif programming_language == "R":
            packages = ["dplyr", "ggplot2", "tidyr", "readr"]
            return "\n".join([f"library({pkg})" for pkg in random.sample(packages, random.randint(1, 3))])
        else:
            return ""

    def generate_complete_test_scenario(self, generation_id: int = None) -> Dict[str, Any]:
        """Generate complete test scenario data"""
        if generation_id is None:
            generation_id = self.generation_counter
            self.generation_counter += 1
        
        scenario = random.choice(self.scenarios)
        
        # Generate base data
        dynamic_generation = self.generate_dynamic_generation(generation_id)
        nodes = self.generate_nodes(generation_id, count=random.randint(3, 6))
        
        # Generate branches
        branches = []
        for i in range(random.randint(1, 3)):
            branch = self.generate_branch(generation_id, nodes[-1]["id"])
            branches.append(branch)
        
        # Generate LLM interaction data
        llm_interactions = []
        
        # Dynamic Generation interactions
        for i, node in enumerate(nodes[1:], 1):  # Skip the first node (start node)
            prompt_data = self.generate_s3_prompt_data(scenario)
            output_data = self.generate_s3_output_data()
            
            llm_interactions.append({
                "type": "dynamic_generation",
                "node_id": node["id"],
                "s3_prompt_data": prompt_data,
                "s3_output_data": output_data,
                "timestamp": int(node["created_time"].timestamp() * 1000)
            })
        
        # Bug Fixer interactions (randomly generated for some nodes)
        for node in random.sample(nodes[1:], random.randint(0, len(nodes)//2)):
            if random.choice([True, False]):  # 50% chance of a bug fixer
                retry_data = self.generate_retry_session_data(node["id"], random.randint(8000, 9999))
                
                llm_interactions.append({
                    "type": "bug_fixer",
                    "node_id": node["id"],
                    "retry_process_id": random.randint(9000, 9999),
                    "computation_id": random.randint(8000, 8999),
                    "s3_session_data": retry_data,
                    "timestamp": int((node["created_time"] + timedelta(minutes=5)).timestamp() * 1000)
                })
        
        # Sort interactions by time
        llm_interactions.sort(key=lambda x: x["timestamp"])
        
        return {
            "scenario": scenario,
            "dynamic_generation": dynamic_generation,
            "branches": branches,
            "nodes": nodes,
            "llm_interactions": llm_interactions,
            "summary": {
                "total_nodes": len(nodes),
                "total_branches": len(branches), 
                "total_interactions": len(llm_interactions),
                "interaction_types": {
                    "dynamic_generation": len([x for x in llm_interactions if x["type"] == "dynamic_generation"]),
                    "bug_fixer": len([x for x in llm_interactions if x["type"] == "bug_fixer"])
                }
            }
        }

    def save_test_data(self, data: Dict[str, Any], filename: str = None):
        """Save test data to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_data_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ Test data saved to: {filename}")


def main():
    """Main function: generate example test data"""
    generator = TestDataGenerator()
    
    print("🔧 Generating Dynamic Generation LLM Monitor test data")
    print("=" * 60)
    
    # Generate multiple test scenarios
    test_scenarios = []
    for i in range(3):
        scenario_data = generator.generate_complete_test_scenario()
        test_scenarios.append(scenario_data)
        
        print(f"📋 Scenario {i+1}: {scenario_data['scenario']}")
        print(f"   Nodes: {scenario_data['summary']['total_nodes']}")
        print(f"   Branches: {scenario_data['summary']['total_branches']}")
        print(f"   Interactions: {scenario_data['summary']['total_interactions']}")
        print(f"   - Dynamic Generation: {scenario_data['summary']['interaction_types']['dynamic_generation']}")
        print(f"   - Bug Fixer: {scenario_data['summary']['interaction_types']['bug_fixer']}")
        print()
    
    # Save all test data
    all_test_data = {
        "generated_at": datetime.now().isoformat(),
        "description": "Dynamic Generation LLM Monitor functional test dataset",
        "scenarios": test_scenarios
    }
    
    generator.save_test_data(all_test_data, "tests/test_data_complete.json")
    
    # Generate standalone data type examples
    examples = {
        "dynamic_generation_example": generator.generate_dynamic_generation(),
        "branch_example": generator.generate_branch(12345),
        "nodes_example": generator.generate_nodes(12345, 4),
        "s3_prompt_example": generator.generate_s3_prompt_data(),
        "s3_output_example": generator.generate_s3_output_data(),
        "retry_session_example": generator.generate_retry_session_data(1001, 8001)
    }
    
    generator.save_test_data(examples, "tests/test_data_examples.json")
    
    print("🎉 Test data generation complete!")
    print("\nGenerated files:")
    print("- tests/test_data_complete.json (complete test scenarios)")
    print("- tests/test_data_examples.json (data type examples)")


if __name__ == "__main__":
    main()