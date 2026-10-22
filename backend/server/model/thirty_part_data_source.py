# CREATE TABLE `thirty_part_data_source` (
#   `id` varchar(255) NOT NULL COMMENT 'Primary Key',
#   `assay` text COMMENT 'Assay',
#   `cell_count` int DEFAULT NULL COMMENT 'Cell Count',
#   `cell_type` text COMMENT 'Cell Type',
#   `cell_type_ancestors` text COMMENT 'Cell Type Ancestors',
#   `collection_id` varchar(255) DEFAULT NULL COMMENT 'Collection Id',
#   `created_at` float DEFAULT NULL COMMENT 'Created At',
#   `dataset_assets` text COMMENT 'Dataset Assets',
#   `dataset_deployments` text COMMENT 'Dataset Deployments',
#   `development_stage` text COMMENT 'Development Stage',
#   `development_stage_ancestors` text COMMENT 'Development Stage Ancestors',
#   `disease` text COMMENT 'Disease',
#   `donor_id` text COMMENT 'Donor Id',
#   `explorer_url` varchar(255) DEFAULT NULL COMMENT 'Explorer Url',
#   `is_primary_data` varchar(255) DEFAULT NULL COMMENT 'Is Primary Data',
#   `is_valid` tinyint(1) DEFAULT NULL COMMENT 'Is Valid',
#   `mean_genes_per_cell` float DEFAULT NULL COMMENT 'Mean Genes Per Cell',
#   `name` varchar(255) DEFAULT NULL COMMENT 'Name',
#   `organism` text COMMENT 'Organism',
#   `primary_cell_count` int DEFAULT NULL COMMENT 'Primary Cell Count',
#   `processing_status` text COMMENT 'Processing Status',
#   `published` tinyint(1) DEFAULT NULL COMMENT 'Published',
#   `published_at` float DEFAULT NULL COMMENT 'Published At',
#   `revision` int DEFAULT NULL COMMENT 'Revision',
#   `schema_version` varchar(255) DEFAULT NULL COMMENT 'Schema Version',
#   `self_reported_ethnicity` text COMMENT 'Self Reported',
#   `sex` text COMMENT 'Sex',
#   `suspension_type` varchar(255) DEFAULT NULL COMMENT 'Suspension Type',
#   `tissue` text COMMENT 'Tissue',
#   `tissue_ancestors` text COMMENT 'Tissue Ancestors',
#   `tombstone` tinyint(1) DEFAULT NULL COMMENT 'Tombstone',
#   `updated_at` float DEFAULT NULL COMMENT 'Updated At',
#   `s3_info` text,
#   PRIMARY KEY (`id`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3

from db import alchemy_db
import json

class ThirtyPartDataSource(alchemy_db.Model):
    __tablename__ = 'thirty_part_data_source'
    id = alchemy_db.Column(alchemy_db.String(255), primary_key=True)
    assay = alchemy_db.Column(alchemy_db.Text)
    cell_count = alchemy_db.Column(alchemy_db.Integer)
    cell_type = alchemy_db.Column(alchemy_db.Text)
    cell_type_ancestors = alchemy_db.Column(alchemy_db.Text)
    collection_id = alchemy_db.Column(alchemy_db.String(255))
    created_at = alchemy_db.Column(alchemy_db.Float)
    dataset_assets = alchemy_db.Column(alchemy_db.Text)
    dataset_deployments = alchemy_db.Column(alchemy_db.Text)
    development_stage = alchemy_db.Column(alchemy_db.Text)
    development_stage_ancestors = alchemy_db.Column(alchemy_db.Text)
    disease = alchemy_db.Column(alchemy_db.Text)
    donor_id = alchemy_db.Column(alchemy_db.Text)
    explorer_url = alchemy_db.Column(alchemy_db.String(255))
    is_primary_data = alchemy_db.Column(alchemy_db.String(255))
    is_valid = alchemy_db.Column(alchemy_db.Boolean)
    mean_genes_per_cell = alchemy_db.Column(alchemy_db.Float)
    name = alchemy_db.Column(alchemy_db.String(255))
    organism = alchemy_db.Column(alchemy_db.Text)
    primary_cell_count = alchemy_db.Column(alchemy_db.Integer)
    processing_status = alchemy_db.Column(alchemy_db.Text)
    published = alchemy_db.Column(alchemy_db.Boolean)
    published_at = alchemy_db.Column(alchemy_db.Float)
    revision = alchemy_db.Column(alchemy_db.Integer)
    schema_version = alchemy_db.Column(alchemy_db.String(255))
    self_reported_ethnicity = alchemy_db.Column(alchemy_db.Text)
    sex = alchemy_db.Column(alchemy_db.Text)
    suspension_type = alchemy_db.Column(alchemy_db.String(255))
    tissue = alchemy_db.Column(alchemy_db.Text)
    tissue_ancestors = alchemy_db.Column(alchemy_db.Text)
    tombstone = alchemy_db.Column(alchemy_db.Boolean)
    updated_at = alchemy_db.Column(alchemy_db.Float)
    s3_info = alchemy_db.Column(alchemy_db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'assay': None if self.assay is None else json.loads(self.assay),
            'cellCount': self.cell_count,
            'cellType': None if self.cell_type is None else json.loads(self.cell_type),
            'cellTypeAncestors': None if self.cell_type_ancestors is None else json.loads(self.cell_type_ancestors),
            'collectionId': self.collection_id,
            'createdAt': self.created_at,
            'datasetAssets': None if self.dataset_assets is None else json.loads(self.dataset_assets),
            'datasetDeployments': None if self.dataset_deployments is None else json.loads(self.dataset_deployments),
            'developmentStage': None if self.development_stage is None else json.loads(self.development_stage),
            'developmentStageAncestors': None if self.development_stage_ancestors is None else json.loads(self.development_stage_ancestors),
            'disease': None if self.disease is None else json.loads(self.disease),
            'donorId': None if self.donor_id is None else json.loads(self.donor_id),
            'explorerUrl': self.explorer_url,
            'isPrimaryData': self.is_primary_data,
            'isValid': self.is_valid,
            'meanGenesPerCell': self.mean_genes_per_cell,
            'name': self.name,
            'organism': None if self.organism is None else json.loads(self.organism),
            'primaryCellCount': self.primary_cell_count,
            'processingStatus': None if self.processing_status is None else json.loads(self.processing_status),
            'published': self.published,
            'publishedAt': self.published_at,
            'revision': self.revision,
            'schemaVersion': self.schema_version,
            'selfReportedEthnicity': None if self.self_reported_ethnicity is None else json.loads(self.self_reported_ethnicity),
            'sex': None if self.sex is None else json.loads(self.sex),
            'suspensionType': None if self.suspension_type is None else json.loads(self.suspension_type),
            'tissue': None if self.tissue is None else json.loads(self.tissue),
            'tissueAncestors': None if self.tissue_ancestors is None else json.loads(self.tissue_ancestors),
            'tombstone': self.tombstone,
            'updatedAt': self.updated_at,
            's3Info': None if self.s3_info is None else json.loads(self.s3_info)
        }