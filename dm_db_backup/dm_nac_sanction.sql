CREATE DATABASE  IF NOT EXISTS `dm_nac` /*!40100 DEFAULT CHARACTER SET utf8 */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `dm_nac`;
-- MySQL dump 10.13  Distrib 8.0.12, for macos10.13 (x86_64)
--
-- Host: 127.0.0.1    Database: dm_nac
-- ------------------------------------------------------
-- Server version	8.0.28

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
 SET NAMES utf8 ;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `sanction`
--

DROP TABLE IF EXISTS `sanction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `sanction` (
  `id` int NOT NULL AUTO_INCREMENT,
  `customer_id` varchar(250) DEFAULT NULL,
  `sanctin_ref_id` varchar(250) DEFAULT NULL,
  `status` varchar(250) DEFAULT NULL,
  `stage` varchar(250) DEFAULT NULL,
  `reject_reason` varchar(250) DEFAULT NULL,
  `bureau_fetch_status` varchar(250) DEFAULT NULL,
  `mobile` varchar(250) DEFAULT NULL,
  `first_name` varchar(250) DEFAULT NULL,
  `last_name` varchar(250) DEFAULT NULL,
  `father_name` varchar(250) DEFAULT NULL,
  `gender` varchar(250) DEFAULT NULL,
  `id_proof_type_from_partner` varchar(250) DEFAULT NULL,
  `id_proof_number_from_partner` varchar(250) DEFAULT NULL,
  `address_proof_type_from_partner` varchar(250) DEFAULT NULL,
  `address_proof_number_from_partner` varchar(250) DEFAULT NULL,
  `dob` varchar(250) DEFAULT NULL,
  `owned_vehicle` varchar(250) DEFAULT NULL,
  `curr_door_and_building` varchar(250) DEFAULT NULL,
  `curr_street_and_locality` varchar(250) DEFAULT NULL,
  `curr_landmark` varchar(250) DEFAULT NULL,
  `curr_city` varchar(250) DEFAULT NULL,
  `curr_district` varchar(250) DEFAULT NULL,
  `curr_state` varchar(250) DEFAULT NULL,
  `curr_pincode` varchar(250) DEFAULT NULL,
  `perm_door_and_building` varchar(250) DEFAULT NULL,
  `perm_landmark` varchar(250) DEFAULT NULL,
  `perm_city` varchar(250) DEFAULT NULL,
  `perm_district` varchar(250) DEFAULT NULL,
  `perm_state` varchar(250) DEFAULT NULL,
  `perm_pincode` varchar(250) DEFAULT NULL,
  `occupation` varchar(250) DEFAULT NULL,
  `company_name` varchar(250) DEFAULT NULL,
  `gross_monthly_income` int DEFAULT NULL,
  `net_monthly_income` int DEFAULT NULL,
  `income_validation_status` varchar(250) DEFAULT NULL,
  `pan` varchar(250) DEFAULT NULL,
  `purpose_of_loan` varchar(250) DEFAULT NULL,
  `loan_amount` int DEFAULT NULL,
  `interest_rate` int DEFAULT NULL,
  `schedule_start_date` varchar(250) DEFAULT NULL,
  `first_installment_date` varchar(250) DEFAULT NULL,
  `total_processing_fees` int DEFAULT NULL,
  `gst` int DEFAULT NULL,
  `pre_emi_amount` int DEFAULT NULL,
  `emi` int DEFAULT NULL,
  `emi_date` varchar(250) DEFAULT NULL,
  `emi_week` int DEFAULT NULL,
  `repayment_frequency` varchar(250) DEFAULT NULL,
  `repayment_mode` varchar(250) DEFAULT NULL,
  `tenure_value` int DEFAULT NULL,
  `tenure_units` varchar(250) DEFAULT NULL,
  `product_name` varchar(250) DEFAULT NULL,
  `primary_bank_account` varchar(250) DEFAULT NULL,
  `bank_name` varchar(250) DEFAULT NULL,
  `mode_of_salary` varchar(250) DEFAULT NULL,
  `client_id` varchar(250) DEFAULT NULL,
  `dedupe_reference_id` varchar(250) DEFAULT NULL,
  `email` varchar(250) DEFAULT NULL,
  `middle_name` varchar(250) DEFAULT NULL,
  `marital_status` varchar(250) DEFAULT NULL,
  `loan_id` varchar(250) DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sanction`
--

LOCK TABLES `sanction` WRITE;
/*!40000 ALTER TABLE `sanction` DISABLE KEYS */;
INSERT INTO `sanction` VALUES (1,'5122691035254046',NULL,'REJECTED','CKYC','SYSTEM_ERROR','COMPLETED',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2022-06-01 16:46:09'),(2,'5169008382430806',NULL,'REJECTED','CKYC','SYSTEM_ERROR','COMPLETED',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2022-06-01 16:49:22');
/*!40000 ALTER TABLE `sanction` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-06-20 12:35:47
