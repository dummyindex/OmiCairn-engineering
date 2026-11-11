"""
Controller for RAG vector store operations
API endpoints for RAG vector store management and querying
"""
from flask import Blueprint, request
from flask_restful import Api, Resource
from service.fix_experience_rag_vector_store import get_fix_experience_vector_store
from service.code_library_rag_vector_store import get_code_library_vector_store
from service.domain_knowledge_rag_vector_store import get_domain_knowledge_vector_store
from dao.fix_description import fix_description_dao
from dao.function_block_v1 import function_block_v1_dao
from log.logger_factory import LoggerFactory
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from datetime import datetime

logger = LoggerFactory.get_logger("rag_controller")


class SearchFixExperienceAPI(Resource):
    @exception_wrapper
    def post(self):
        """
        Search for similar error fixes in RAG vector store
        
        Request body:
        {
            "error_info": "error stack trace or message",
            "top_k": 5,  // optional, default 5
            "error_type_filter": "ValueError"  // optional
        }
        
        Response:
        {
            "success": true,
            "results": [
                {
                    "fix_id": 1,
                    "computation_id": 123,
                    "error_type": "ValueError",
                    "normalized_error": "...",
                    "original_error": "...",
                    "fix_strategy": "...",
                    "created_at": "2024-01-01T12:00:00",
                    "similarity_score": 0.95
                },
                ...
            ],
            "count": 5
        }
        """
        request_auditor.request_json_check(request, ["error_info"])
        data = request.get_json()
        error_info = data.get('error_info')
        top_k = data.get('top_k', 5)
        error_type_filter = data.get('error_type_filter')
        
        # Get the RAG vector store instance
        rag_store = get_fix_experience_vector_store()
        
        # Search for similar fix solutions
        results = rag_store.search_similar_fixes(
            error_info=error_info,
            top_k=top_k,
            error_type_filter=error_type_filter
        )
        
        return ResponseManager.new_success_response(data={
            "results": results,
            "count": len(results)
        })


class FixExperienceVectorStoreStatsGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        Get RAG vector store statistics
        
        Response:
        {
            "success": true,
            "stats": {
                "collection_name": "fix_experience",
                "total_documents": 100,
                "status": "healthy"
            }
        }
        """
        rag_store = get_fix_experience_vector_store()
        stats = rag_store.get_collection_stats()
        
        return ResponseManager.new_success_response(data=stats)


class SyncFixesRagVectorStoreAPI(Resource):
    @exception_wrapper
    def post(self):
        """
        Manually trigger RAG vector store sync (called by daemon process)
        
        Response:
        {
            "success": true,
            "message": "Sync completed successfully",
            "stats": {
                "success": 10,
                "failure": 0,
                "total_documents": 100
            }
        }
        """
        rag_store = get_fix_experience_vector_store()
        
        # Get the last sync time
        last_sync_time = rag_store.get_last_sync_timestamp()
        logger.info(f"Starting RAG sync from timestamp: {last_sync_time.isoformat()}")
        
        # Query new fix descriptions
        new_fix_descriptions = fix_description_dao.find_fix_descriptions_after_timestamp(last_sync_time)

        if not new_fix_descriptions:
            logger.info("No new fix descriptions to sync")
            stats = rag_store.get_collection_stats()
            return ResponseManager.new_success_response(data={
                "message": "No new data to sync",
                "stats": {
                    "success": 0,
                    "failure": 0,
                    "total_documents": stats.get('total_documents', 0)
                }
            })
        
        logger.info(f"Found {len(new_fix_descriptions)} new fix descriptions")
        
        # Prepare data
        fix_desc_list = []
        for fix_desc in new_fix_descriptions:
            fix_desc_list.append({
                'id': fix_desc.id,
                'computation_id': fix_desc.computation_id,
                'error_info': fix_desc.error_info,
                'fix_strategy': fix_desc.fix_strategy,
                'created_at': fix_desc.created_at
            })
        
        # Batch-add to the vector store
        result = rag_store.batch_add_fix_descriptions(fix_desc_list)
        
        # Update the last sync time
        if new_fix_descriptions:
            latest_timestamp = max(fix_desc.created_at for fix_desc in new_fix_descriptions)
            rag_store.save_last_sync_timestamp(latest_timestamp)
            logger.info(f"Updated last sync timestamp to: {latest_timestamp.isoformat()}")
        
        # Get the total count
        stats = rag_store.get_collection_stats()
        
        logger.info(f"RAG sync completed: {result['success']} succeeded, {result['failure']} failed")
        
        return ResponseManager.new_success_response(data={
            "message": f"Synced {result['success']} fix descriptions",
            "stats": {
                "success": result['success'],
                "failure": result['failure'],
                "total_documents": stats.get('total_documents', 0)
            }
        })


class FixExperienceSyncStatusGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        Get RAG sync status
        
        Response:
        {
            "success": true,
            "status": {
                "last_sync_timestamp": "2024-01-01T12:00:00",
                "total_documents": 100,
                "collection_status": "healthy"
            }
        }
        """
        rag_store = get_fix_experience_vector_store()
        
        last_sync_time = rag_store.get_last_sync_timestamp()
        stats = rag_store.get_collection_stats()
        
        return ResponseManager.new_success_response(data={
            "last_sync_timestamp": last_sync_time.isoformat(),
            "total_documents": stats.get('total_documents', 0),
            "collection_status": stats.get('status', 'unknown')
        })


class SearchCodeLibraryAPI(Resource):
    @exception_wrapper
    def post(self):
        """
        Search for similar code in the code library
        
        Request body:
        {
            "query": "code snippet or description",
            "top_k": 5,  // optional, default 5
            "function_block_name_filter": "MyFunction"  // optional
        }
        
        Response:
        {
            "success": true,
            "results": [
                {
                    "version_id": 1,
                    "function_block_id": 10,
                    "function_block_name": "MyFunction",
                    "description": "...",
                    "code_preview": "...",
                    "created_time": "2024-01-01T12:00:00",
                    "similarity_score": 0.95,
                    "full_text": "..."
                },
                ...
            ],
            "count": 5
        }
        """
        request_auditor.request_json_check(request, ["query"])
        data = request.get_json()
        query = data.get('query')
        top_k = data.get('top_k', 5)
        function_block_name_filter = data.get('function_block_name_filter')
        
        # Get the Code Library RAG vector store instance
        rag_store = get_code_library_vector_store()
        
        # Search for similar code
        results = rag_store.search_similar_code(
            query=query,
            top_k=top_k,
            function_block_name_filter=function_block_name_filter
        )
        
        return ResponseManager.new_success_response(data={
            "results": results,
            "count": len(results)
        })


class CodeLibraryVectorStoreStatsGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        Get Code Library RAG vector store statistics
        
        Response:
        {
            "success": true,
            "stats": {
                "collection_name": "code_library",
                "total_documents": 100,
                "status": "healthy"
            }
        }
        """
        rag_store = get_code_library_vector_store()
        stats = rag_store.get_collection_stats()
        
        return ResponseManager.new_success_response(data=stats)


class SyncCodeLibraryRagVectorStoreAPI(Resource):
    @exception_wrapper
    def post(self):
        """
        Manually trigger Code Library RAG vector store sync (called by daemon process)
        
        Response:
        {
            "success": true,
            "message": "Sync completed successfully",
            "stats": {
                "success": 10,
                "failure": 0,
                "total_documents": 100
            }
        }
        """
        rag_store = get_code_library_vector_store()
        
        # Get the last sync time
        last_sync_time = rag_store.get_last_sync_timestamp()
        logger.info(f"Starting Code Library RAG sync from timestamp: {last_sync_time.isoformat()}")
        
        # Query new code versions (user_id=0 denotes the public code library)
        new_code_versions = function_block_v1_dao.find_versions_by_user_id_and_created_time(
            user_id=0,
            start_datetime=last_sync_time,
            end_datetime=datetime.now()
        )

        new_code_versions = [v for v in new_code_versions if v.get("is_v2") == True]
        logger.info(f"Filtered to {len(new_code_versions)} v2 code versions")

        if not new_code_versions:
            logger.info("No new code versions to sync")
            stats = rag_store.get_collection_stats()
            return ResponseManager.new_success_response(data={
                "message": "No new data to sync",
                "stats": {
                    "success": 0,
                    "failure": 0,
                    "total_documents": stats.get('total_documents', 0)
                }
            })
        
        logger.info(f"Found {len(new_code_versions)} new code versions")
        
        # Batch-add to the vector store
        result = rag_store.batch_add_code_versions(new_code_versions)
        
        # Update the last sync time
        if new_code_versions:
            # Extract created_time from the dict
            latest_timestamp = max(
                datetime.fromisoformat(v['created_time']) if isinstance(v['created_time'], str) 
                else v['created_time'] 
                for v in new_code_versions
            )
            rag_store.save_last_sync_timestamp(latest_timestamp)
            logger.info(f"Updated last sync timestamp to: {latest_timestamp.isoformat()}")
        
        # Get the total count
        stats = rag_store.get_collection_stats()
        
        logger.info(f"Code Library RAG sync completed: {result['success']} succeeded, {result['failure']} failed")
        
        return ResponseManager.new_success_response(data={
            "message": f"Synced {result['success']} code versions",
            "stats": {
                "success": result['success'],
                "failure": result['failure'],
                "total_documents": stats.get('total_documents', 0)
            }
        })


class CodeLibrarySyncStatusGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        Get Code Library RAG sync status
        
        Response:
        {
            "success": true,
            "status": {
                "last_sync_timestamp": "2024-01-01T12:00:00",
                "total_documents": 100,
                "collection_status": "healthy"
            }
        }
        """
        rag_store = get_code_library_vector_store()
        
        last_sync_time = rag_store.get_last_sync_timestamp()
        stats = rag_store.get_collection_stats()
        
        return ResponseManager.new_success_response(data={
            "last_sync_timestamp": last_sync_time.isoformat(),
            "total_documents": stats.get('total_documents', 0),
            "collection_status": stats.get('status', 'unknown')
        })


class SearchDomainKnowledgeAPI(Resource):
    @exception_wrapper
    def post(self):
        """
        Search for similar domain knowledge in the RAG vector store
        
        Request body:
        {
            "query": "search query or description",
            "top_k": 5  // optional, default 5
        }
        
        Response:
        {
            "success": true,
            "results": [
                {
                    "object_key": "domain-knowledge/example.json",
                    "name": "Example Knowledge",
                    "description": "...",
                    "text": "...",
                    "last_modified": "2024-01-01T12:00:00",
                    "similarity_score": 0.95,
                    "searchable_text": "..."
                },
                ...
            ],
            "count": 5
        }
        """
        request_auditor.request_json_check(request, ["query"])
        data = request.get_json()
        query = data.get('query')
        top_k = data.get('top_k', 5)
        
        # Get the Domain Knowledge RAG vector store instance
        rag_store = get_domain_knowledge_vector_store()
        
        # Search for similar knowledge
        results = rag_store.search_similar_knowledge(
            query=query,
            top_k=top_k
        )
        
        return ResponseManager.new_success_response(data={
            "results": results,
            "count": len(results)
        })


class DomainKnowledgeVectorStoreStatsGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        Get Domain Knowledge RAG vector store statistics
        
        Response:
        {
            "success": true,
            "stats": {
                "collection_name": "domain_knowledge",
                "total_documents": 100,
                "status": "healthy"
            }
        }
        """
        rag_store = get_domain_knowledge_vector_store()
        stats = rag_store.get_collection_stats()
        
        return ResponseManager.new_success_response(data=stats)


class SyncDomainKnowledgeRagVectorStoreAPI(Resource):
    @exception_wrapper
    def post(self):
        """
        Manually trigger Domain Knowledge RAG vector store sync (called by daemon process)
        
        Response:
        {
            "success": true,
            "message": "Sync completed successfully",
            "stats": {
                "success": 10,
                "failure": 0,
                "total_documents": 100
            }
        }
        """
        rag_store = get_domain_knowledge_vector_store()
        
        # Get the last sync time
        last_sync_time = rag_store.get_last_sync_timestamp()
        logger.info(f"Starting Domain Knowledge RAG sync from timestamp: {last_sync_time.isoformat()}")
        
        # Fetch new or updated files from S3
        knowledge_items = rag_store.fetch_s3_files_with_metadata(last_sync_time)

        if not knowledge_items:
            logger.info("No new domain knowledge files to sync")
            stats = rag_store.get_collection_stats()
            return ResponseManager.new_success_response(data={
                "message": "No new data to sync",
                "stats": {
                    "success": 0,
                    "failure": 0,
                    "total_documents": stats.get('total_documents', 0)
                }
            })
        
        logger.info(f"Found {len(knowledge_items)} new or updated domain knowledge files")
        
        # Batch-add to the vector store
        result = rag_store.batch_add_domain_knowledge(knowledge_items)
        
        # Update the last sync time
        if knowledge_items:
            # Find the latest file modification time
            latest_timestamp = max(
                item['last_modified'].replace(tzinfo=None) if item.get('last_modified') 
                else datetime.now()
                for item in knowledge_items
            )
            rag_store.save_last_sync_timestamp(latest_timestamp)
            logger.info(f"Updated last sync timestamp to: {latest_timestamp.isoformat()}")
        
        # Get the total count
        stats = rag_store.get_collection_stats()
        
        logger.info(f"Domain Knowledge RAG sync completed: {result['success']} succeeded, {result['failure']} failed")
        
        return ResponseManager.new_success_response(data={
            "message": f"Synced {result['success']} domain knowledge items",
            "stats": {
                "success": result['success'],
                "failure": result['failure'],
                "total_documents": stats.get('total_documents', 0)
            }
        })


class DomainKnowledgeSyncStatusGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        Get Domain Knowledge RAG sync status
        
        Response:
        {
            "success": true,
            "status": {
                "last_sync_timestamp": "2024-01-01T12:00:00",
                "total_documents": 100,
                "collection_status": "healthy"
            }
        }
        """
        rag_store = get_domain_knowledge_vector_store()
        
        last_sync_time = rag_store.get_last_sync_timestamp()
        stats = rag_store.get_collection_stats()
        
        return ResponseManager.new_success_response(data={
            "last_sync_timestamp": last_sync_time.isoformat(),
            "total_documents": stats.get('total_documents', 0),
            "collection_status": stats.get('status', 'unknown')
        })


rag_bp = Blueprint("rag", __name__)
rag_api = Api(rag_bp, "/rag")

# Fix Experience APIs
rag_api.add_resource(SearchFixExperienceAPI, "/search-fix-experience")
rag_api.add_resource(FixExperienceVectorStoreStatsGetAPI, "/fix-experience-stats")
rag_api.add_resource(SyncFixesRagVectorStoreAPI, "/sync-fix-experience")
rag_api.add_resource(FixExperienceSyncStatusGetAPI, "/fix-experience-sync-status")

# Code Library APIs
rag_api.add_resource(SearchCodeLibraryAPI, "/search-code-library")
rag_api.add_resource(CodeLibraryVectorStoreStatsGetAPI, "/code-library-stats")
rag_api.add_resource(SyncCodeLibraryRagVectorStoreAPI, "/sync-code-library")
rag_api.add_resource(CodeLibrarySyncStatusGetAPI, "/code-library-sync-status")

# Domain Knowledge APIs
rag_api.add_resource(SearchDomainKnowledgeAPI, "/search-domain-knowledge")
rag_api.add_resource(DomainKnowledgeVectorStoreStatsGetAPI, "/domain-knowledge-stats")
rag_api.add_resource(SyncDomainKnowledgeRagVectorStoreAPI, "/sync-domain-knowledge")
rag_api.add_resource(DomainKnowledgeSyncStatusGetAPI, "/domain-knowledge-sync-status")
