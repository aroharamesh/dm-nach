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
-- Table structure for table `sanction_fileupload`
--

DROP TABLE IF EXISTS `sanction_fileupload`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `sanction_fileupload` (
  `id` int NOT NULL AUTO_INCREMENT,
  `customer_id` varchar(250) DEFAULT NULL,
  `file_name` varchar(250) DEFAULT NULL,
  `message` varchar(2000) DEFAULT NULL,
  `status` varchar(250) DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sanction_fileupload`
--

LOCK TABLES `sanction_fileupload` WRITE;
/*!40000 ALTER TABLE `sanction_fileupload` DISABLE KEYS */;
INSERT INTO `sanction_fileupload` VALUES (1,'5276656237789585','Screenshot 2022-05-30 at 2.16.11 PM.png','SUCCESS',NULL,'2022-06-01 13:26:35'),(2,'5276656237789585','Screenshot 2022-05-30 at 2.16.11 PM.png','File Replaced Successfully : AADHAR_DOC','SUCCESS','2022-06-01 13:28:52'),(3,'5276656237789585','Screenshot 2022-05-30 at 2.16.11 PM.png','File Replaced Successfully : VOTER_CARD','SUCCESS','2022-06-01 13:29:08');
/*!40000 ALTER TABLE `sanction_fileupload` ENABLE KEYS */;
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
