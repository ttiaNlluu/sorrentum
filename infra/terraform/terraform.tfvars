# <--- ./provider --->

region  = "eu-north-1"
profile = "ck"



# <--- ./modules/vpc --->

vpc_cidr             = "172.30.0.0/16"
enable_dns_support   = true
enable_dns_hostnames = true
instance_tenancy     = "default"
vpc_tags             = { Name = "prod-vpc-1" }
security_groups = [
  {
    name        = "ext-sg-1"
    description = "Allow OpenVPN from internet and ALL outbound"
    tags = {
      Name = "ext-sg-1"
    }
    ingress = [
      {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        description = "Allow anything from EU servers"
        cidr_blocks = ["172.30.0.0/16"]
      },
      {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        description = "Allow anything from US servers"
        cidr_blocks = ["172.29.0.0/16"]
      },
      {
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        description = "ssh shayan workaround"
        cidr_blocks = ["0.0.0.0/0"]
      },
      {
        from_port   = 1194
        to_port     = 1194
        protocol    = "udp"
        description = "Allow OpenVPN from Internet"
        cidr_blocks = ["0.0.0.0/0"]
      },
      {
        from_port   = 8
        to_port     = -1
        protocol    = "icmp"
        description = "Allow ICMP reply from Internet"
        cidr_blocks = ["0.0.0.0/0"]
      },
    ]
    egress = [
      {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        description = "Allow ANY to Internet"
        cidr_blocks = ["0.0.0.0/0"]
      },
      {
        from_port   = 10051
        to_port     = 10051
        protocol    = "tcp"
        description = "Allow Zabbix agent communication to Zabbix server"
        cidr_blocks = ["172.30.3.65/32"]
      },
    ]
  },
  {
    name        = "int-sg-1"
    description = "Allow ALL from VPN user pool and ALL outbound"
    tags = {
      Name = "int-sg-1"
    }
    ingress = [
      {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        description = "Allow ALL from US servers"
        cidr_blocks = ["172.29.0.0/16"]
      },
      {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        description = "Allow ALL from EU servers"
        cidr_blocks = ["172.30.0.0/16"]
      }
    ]
    egress = [
      {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        description = "Allow ANY to Internet"
        cidr_blocks = ["0.0.0.0/0"]
      }
    ]
  },
  {
    name        = "int-sg-2"
    description = "Zabbix SG"
    tags        = { Name = "int-sg-2" }
    ingress = [
      {
        from_port   = 80
        to_port     = 80
        protocol    = "tcp"
        description = "Allow HTTP from whole EU region"
        cidr_blocks = ["172.30.0.0/16"]
      },
      {
        from_port   = 80
        to_port     = 80
        protocol    = "tcp"
        description = "Allow HTTPS from whole US region"
        cidr_blocks = ["172.29.0.0/16"]
      },
      {
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        description = "Allow SSH from whole EU region"
        cidr_blocks = ["172.30.0.0/16"]
      },
      {
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        description = "Allow SSH from whole US region"
        cidr_blocks = ["172.29.0.0/16"]
      },
      {
        from_port   = 10051
        to_port     = 10051
        protocol    = "tcp"
        description = "Allow ZABBIX Agent from whole EU region"
        cidr_blocks = ["172.30.0.0/16"]
      },
      {
        from_port   = 10051
        to_port     = 10051
        protocol    = "tcp"
        description = "Allow ZABBIX Agent from whole US region"
        cidr_blocks = ["172.29.0.0/16"]
      },
      {
        from_port   = 443
        to_port     = 443
        protocol    = "tcp"
        description = "Allow HTTPS from whole EU region"
        cidr_blocks = ["172.30.0.0/16"]
      },
      {
        from_port   = 443
        to_port     = 443
        protocol    = "tcp"
        description = "Allow HTTPS from whole US region"
        cidr_blocks = ["172.29.0.0/16"]
      }
    ]
    egress = [
      {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        description = ""
        cidr_blocks = ["0.0.0.0/0"]
      },
      {
        from_port   = 10050
        to_port     = 10050
        protocol    = "tcp"
        description = "Allow ZABBIX server to whole EU region"
        cidr_blocks = ["172.30.0.0/16"]
      },
      {
        from_port   = 10050
        to_port     = 10050
        protocol    = "tcp"
        description = "Allow ZABBIX server to whole US region"
        cidr_blocks = ["172.29.0.0/16"]
      }
    ]
  },
  {
    name        = "int-db-1"
    description = "Allow access to DB from VPC"
    tags        = { Name = "int-db-1" }
    ingress = [
      {
        from_port       = 5432
        to_port         = 5432
        protocol        = "tcp"
        description     = "Allow db access from servers in VPC"
        security_groups = ["int-sg-1"]
      }
    ]
    egress = [
      {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        description = ""
        cidr_blocks = ["0.0.0.0/0"]
      }
    ]
  },
  {
    name        = "efs-sg-1"
    description = "EFS sg"
    tags        = { Name = "efs-sg-1" }
    ingress = [
      {
        from_port   = 2049
        to_port     = 2049
        protocol    = "tcp"
        description = "Allow access to Sorrentum VPC"
        cidr_blocks = ["172.31.0.0/16"]
      },
      {
        from_port       = 2049
        to_port         = 2049
        protocol        = "tcp"
        description     = "Allow mount to instances in int-sg-1"
        security_groups = ["int-sg-1"]
      }
    ]
    egress = [
      {
        from_port   = 2049
        to_port     = 2049
        protocol    = "tcp"
        description = "Allow efs to see instances in sorrentum VPC"
        cidr_blocks = ["172.31.0.0/16"]
      },
      {
        from_port       = 2049
        to_port         = 2049
        protocol        = "tcp"
        description     = "Allow efs to see instances in int-sg-1"
        security_groups = ["int-sg-1"]
      }
    ]
  },
]
subnet_availability_zones = ["eu-north-1c", "eu-north-1c", "eu-north-1b", "eu-north-1b"]
subnet_cidr_blocks        = ["172.30.1.0/24", "172.30.2.0/24", "172.30.3.0/24", "172.30.254.0/24"]
subnet_tags = [
  { Name = "public-subnet-1", Created_by = "terraform" },
  { Name = "private-subnet-1", Created_by = "terraform" },
  { Name = "private-subnet-2", Created_by = "terraform" },
  { Name = "vpn-subnet-1", Created_by = "terraform" },
]
subnet_map_public_ip_on_launch = false
internet_gateway_tags          = { Name = "internet-gw-1" }
nat_gateway_name               = "nat-gw-1"
nat_gateway_subnet_id          = "public-subnet-1"
route_tables = [
  {
    tags = { Name = "external-rt-1" }
  },
  {
    tags = { Name = "internal-rt-1" }
  }
]
internet_gateway_routes = [
  {
    destination_cidr_block = "0.0.0.0/0",
    route_table_index      = 0
  }
]
nat_gateway_routes = [
  {
    destination_cidr_block = "0.0.0.0/0",
    nat_gateway_id         = "nat-gw-1",
    route_table_index      = 1
  }
]
instance_routes = [
  {
    destination_cidr_block = "172.30.254.0/24",
    instance_id            = "VPN-terraform",
    route_table_index      = 1
  },
  {
    destination_cidr_block = "172.30.254.0/24",
    instance_id            = "VPN-terraform",
    route_table_index      = 0
  }
]

subnet_route_table_associations = [
  { subnet_index = 0, route_table_index = 0 },
  { subnet_index = 1, route_table_index = 1 },
  { subnet_index = 2, route_table_index = 1 },
  { subnet_index = 3, route_table_index = 1 },
]



# <--- ./modules/ec2 --->

ec2_configs = [
  {
    availability_zone           = "eu-north-1c"
    private_ip                  = "172.30.1.125" # Ensure a different IP
    volume_size                 = 20
    volume_type                 = "standard"
    ami                         = "ami-0cf13cb849b11b451"
    instance_type               = "t3.micro"
    subnet_id                   = "public-subnet-1"
    vpc_security_group_ids      = ["ext-sg-1"]
    associate_public_ip_address = true
    tenancy                     = "default"
    ebs_optimized               = true
    source_dest_check           = false
    delete_on_termination       = true
    instance_name               = "VPN-terraform"
    key_pair_name               = "vpn-keypair"
    iam_instance_profile        = ""
  },
  {
    availability_zone           = "eu-north-1c"
    private_ip                  = "172.30.2.114" # Ensure a different IP
    volume_size                 = 100
    volume_type                 = "gp2"
    ami                         = "ami-0cf13cb849b11b451"
    instance_type               = "t3.xlarge"
    subnet_id                   = "private-subnet-1"
    vpc_security_group_ids      = ["int-sg-1"]
    associate_public_ip_address = false
    tenancy                     = "default"
    ebs_optimized               = true
    source_dest_check           = true
    delete_on_termination       = true
    instance_name               = "Airflow-terraform"
    key_pair_name               = "airflow-keypair"
    iam_instance_profile        = "ProdAirflowEC2Role"
  },
  {
    availability_zone           = "eu-north-1b"
    private_ip                  = "172.30.3.63" # Ensure a different IP
    volume_size                 = 100
    volume_type                 = "gp2"
    ami                         = "ami-0cf13cb849b11b451"
    instance_type               = "t3.small"
    subnet_id                   = "private-subnet-2"
    vpc_security_group_ids      = ["int-sg-2"]
    associate_public_ip_address = false
    tenancy                     = "default"
    ebs_optimized               = true
    source_dest_check           = true
    delete_on_termination       = true
    instance_name               = "Zabbix-terraform"
    key_pair_name               = "zabbix-keypair"
    iam_instance_profile        = ""
  },
]



# <--- ./modules/rds --->

rds_subnet_group_desc                  = "RDS Subnet group - Created by terraform"
rds_subnet_group_name                  = "default-subnet-group"
rds_subnet_ids                         = ["private-subnet-1", "private-subnet-2"]
db_identifier                          = "prod-im-db"
db_allocated_storage                   = 300
db_instance_class                      = "db.r6g.large"
db_engine                              = "postgres"
db_backup_window                       = "06:13-06:43"
db_backup_retention_period             = 0
db_availability_zone                   = "eu-north-1c"
db_maintenance_window                  = "sun:02:29-sun:02:59"
db_multi_az                            = false
db_engine_version                      = "13.10"
db_auto_minor_version_upgrade          = true
db_license_model                       = "postgresql-license"
db_iops                                = 3000
db_publicly_accessible                 = false
db_storage_type                        = "io1"
db_port                                = 5432
db_storage_encrypted                   = true
db_kms_key_id                          = ""
db_copy_tags_to_snapshot               = true
db_monitoring_interval                 = 0
db_iam_database_authentication_enabled = false
db_deletion_protection                 = false
performance_insights_enabled           = false
rds_security_group_ids                 = ["int-sg-1", "int-db-1"]
skip_final_snapshot                    = true



# <--- ./modules/efs --->

efs_performance_mode = "generalPurpose"
efs_encrypted        = true
efs_kms_key_id       = ""
efs_throughput_mode  = "bursting"
efs_name             = "prod-efs-2"
efs_mount_targets = [
  {
    subnet_id       = "private-subnet-1"
    security_groups = ["efs-sg-1"]
    ip_address      = "172.30.2.253"
  },
  {
    subnet_id       = "private-subnet-2"
    security_groups = ["efs-sg-1"]
    ip_address      = "172.30.3.236"
  }
]



# <--- ./modules/iam --->

iam_roles = {
  ProdAirflowEC2Role = { description = "Allows EC2 instance hosting Airflow to call necessary services - CloudWatch, ECS, allow role pass" }
  s3InstanceRole     = { description = "Allows S3 to call AWS services on your behalf." }
}
iam_policies = {
  MFA-ON-CONSOLE_API-VIA-INTERNAL_CLOUDWATCH-RO_VPC            = { description = "Allow access to cloudwatch when request from prod-vpc-1" },
  MFA-ON-CONSOLE_API-VIA-INTERNAL_ECS-FULL-VPC                 = { description = "Allow ECS Access from requests originating from the prod-vpc-1" },
  MFA-ON-CONSOLE_API-VIA-INTERNAL_ECSAllowTaskExeucionRolePass = { description = "" },
  AllowS3Replication                                           = { description = "Access policy which grants privileges to replicate data from production s3 bucket to preprod s3 bucket" },
  S3AllowBatchReplication                                      = { description = "" },
}
iam_role_policies = {
  ProdAirflowEC2Role = [
    "MFA-ON-CONSOLE_API-VIA-INTERNAL_CLOUDWATCH-RO_VPC",
    "MFA-ON-CONSOLE_API-VIA-INTERNAL_ECS-FULL-VPC",
    "MFA-ON-CONSOLE_API-VIA-INTERNAL_ECSAllowTaskExeucionRolePass"
  ]
  s3InstanceRole = [
    "AllowS3Replication",
    "S3AllowBatchReplication"
  ]
}



# <--- ./modules/aws_backup --->

backup_configs = {
  production = {
    name               = "production-backup"
    rule_name          = "TwiceDailyBackup"
    target_vault_name  = "production-backup-vault"
    schedule           = "cron(0 6,18 * * ? *)" # Twice a day
    start_window       = 360
    completion_window  = 1080
    cold_storage_after = 0
    delete_after       = 30
    selection_name     = "production-selection"
    iam_role_arn       = "arn:aws:iam::623860924167:role/service-role/AWSBackupDefaultServiceRole"
    resources          = [""]
    selection_tags     = { key = "Name", value = "Airflow-terraform" }
    force_destroy      = true
  },
  //  preprod = {
  //    name               = "preprod-backup"
  //    rule_name          = "DailyBackup"
  //    target_vault_name  = "preprod-backup-vault"
  //    schedule           = "cron(0 12 * * ? *)" # Once a day
  //    start_window       = 2
  //    completion_window  = 2
  //    cold_storage_after = 7
  //    delete_after       = 7
  //    selection_name     = "preprod-selection"
  //    iam_role_arn       = "arn:aws:iam::623860924167:role/service-role/AWSBackupDefaultServiceRole"
  //    resources          = ["arn:aws:ec2:region:account-id:instance/instance-id"]
  //    selection_tags     = { key = "tag-key", value = "tag-value" }
  //    force_destroy      = true
  //  }
}



# <--- ./modules/s3 --->

buckets = {
  "S3Bucket" = {
    name          = "tf-cryptokaizen-data"
    acl           = "private"
    force_destroy = true
    versioning    = "Enabled"
    lifecycle_rules = [
      {
        id                            = "standard_object_lifecycle_policy"
        enabled                       = true
        prefix                        = ""
        noncurrent_version_expiration = { days = 30 }
        noncurrent_version_transition = { days = 10, storage_class = "INTELLIGENT_TIERING" }
        transition                    = { days = 30, storage_class = "STANDARD_IA" }
      },
      {
        id                            = "db_archive_policy"
        enabled                       = true
        prefix                        = "db_archive"
        noncurrent_version_transition = { days = 30, storage_class = "GLACIER_IR" }
        transition                    = { days = 30, storage_class = "ONEZONE_IA" }
      }
    ]
    replication_configuration = {
      role = "arn:aws:iam::623860924167:role/s3InstanceRole"
      rules = {
        id     = "BackupRule"
        status = "Enabled"
        destination = {
          bucket        = "arn:aws:s3:::tf-cryptokaizen-data.preprod"
          storage_class = null
        }
      }
    }
  },
  "S3Bucket2" = {
    name          = "tf-cryptokaizen-data.preprod"
    acl           = "private"
    force_destroy = true
    versioning    = "Enabled"
    lifecycle_rules = [
      {
        id                            = "standard_preprod_object_lifecycle_policy"
        enabled                       = true
        noncurrent_version_expiration = { days = 30 }
        transition                    = { days = 30, storage_class = "ONEZONE_IA" }
      }
    ]
  },
  "S3Bucket3" = {
    name          = "tf-cryptokaizen-data-access-logs"
    acl           = "private"
    force_destroy = true
    versioning    = "Enabled"
    policy        = "S3Bucket3Policy"
    lifecycle_rules = [
      {
        id         = "audit_lifecycle_policy"
        enabled    = true
        expiration = { days = 180 }
        transition = { days = 60, storage_class = "INTELLIGENT_TIERING" }
      }
    ]
  },
  "S3Bucket4" = {
    name          = "tf-cryptokaizen-data-backup"
    acl           = "private"
    force_destroy = true
    versioning    = "Enabled"
    lifecycle_rules = [
      {
        id                             = "BackupBucketRule"
        enabled                        = true
        noncurrent_version_transitions = { days = 0, storage_class = "GLACIER_IR" }
        transition                     = { days = 0, storage_class = "GLACIER_IR" }
      },
      {
        id                            = "DeleteAllButNewestVersion"
        enabled                       = true
        prefix                        = "efs_archive"
        noncurrent_version_expiration = { days = 1 }
      }
    ]
  },
  "S3Bucket5" = {
    name          = "tf-cryptokaizen-data-test"
    acl           = "private"
    force_destroy = true
    versioning    = "Enabled"
    lifecycle_rules = [
      {
        id                             = "standard_object_lifecycle_policy"
        enabled                        = true
        noncurrent_version_expiration  = { days = 31 }
        noncurrent_version_transitions = { days = 30, storage_class = "GLACIER_IR" }
        transition                     = { days = 30, storage_class = "STANDARD_IA" }
        transition                     = { days = 60, storage_class = "ONEZONE_IA" }
      }
    ]
  },
  "S3Bucket6" = {
    name          = "tf-cryptokaizen-public"
    acl           = "private"
    force_destroy = true
    versioning    = "Enabled"
    policy        = "S3Bucket6Policy"
    public_access_block = {
      block_public_acls       = false
      block_public_policy     = false
      ignore_public_acls      = false
      restrict_public_buckets = false
    }
    lifecycle_rules = []
  },
  "S3Bucket7" = {
    name          = "tf-cryptokaizen-html"
    acl           = "private"
    force_destroy = true
    versioning    = "Enabled"
    policy        = "S3Bucket7Policy"
    lifecycle_rules = [
      {
        id                            = "standard_object_lifecycle_policy"
        enabled                       = true
        noncurrent_version_expiration = { days = 30 }
        noncurrent_version_transition = { days = 10, storage_class = "INTELLIGENT_TIERING" }
        transition                    = { days = 30, storage_class = "ONEZONE_IA" }
      }
    ]
    replication_configuration = {
      role = "arn:aws:iam::623860924167:role/s3InstanceRole"
      rules = {
        id     = "Copy PnL to public bucket"
        status = "Enabled"
        destination = {
          bucket        = "arn:aws:s3:::tf-cryptokaizen-public"
          storage_class = null
        }
      }
    }
  },
  "S3Bucket8" = {
    name          = "tf-cryptokaizen-unit-test"
    acl           = "private"
    force_destroy = true
    versioning    = "Enabled"
    lifecycle_rules = [
      {
        id         = "IntelligentTieringRule"
        enabled    = true
        transition = { days = 0, storage_class = "INTELLIGENT_TIERING" }
      }
    ]
  }
}



# <--- ./data-sources.tf --->

secret_arn = "arn:aws:secretsmanager:eu-north-1:623860924167:secret:ansible/airflow_secrets-g38Ddj" # "arn:aws:secretsmanager:your-region:your-account-id:secret:your-secret-name"
