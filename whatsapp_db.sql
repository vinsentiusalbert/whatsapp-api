-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 13, 2026 at 04:59 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `whatsapp_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `whatsapp_messages`
--

CREATE TABLE `whatsapp_messages` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `direction` enum('INBOUND','OUTBOUND') NOT NULL,
  `message_id` varchar(255) DEFAULT NULL,
  `sender` varchar(100) DEFAULT NULL,
  `receiver` varchar(100) DEFAULT NULL,
  `sender_name` varchar(255) DEFAULT NULL,
  `message_type` varchar(50) DEFAULT 'text',
  `message` text DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `http_status` int(11) DEFAULT NULL,
  `raw_payload` longtext DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `whatsapp_messages`
--

INSERT INTO `whatsapp_messages` (`id`, `direction`, `message_id`, `sender`, `receiver`, `sender_name`, `message_type`, `message`, `status`, `http_status`, `raw_payload`, `created_at`) VALUES
(1, 'OUTBOUND', NULL, '628xxxxxxxx', '6287854710790', NULL, 'text', 'Gelooo keren', 'FAILED', 400, '{\"raw_response\": \"<!DOCTYPE html>\\n<html lang=\\\"en\\\">\\n<head>\\n<meta charset=\\\"utf-8\\\">\\n<title>Error</title>\\n</head>\\n<body>\\n<pre>Bad Request</pre>\\n</body>\\n</html>\\n\"}', '2026-08-13 20:30:46'),
(2, 'OUTBOUND', NULL, '6287854710790', '6287854710790', NULL, 'text', 'Gelooo keren', 'FAILED', 400, '{\"raw_response\": \"<!DOCTYPE html>\\n<html lang=\\\"en\\\">\\n<head>\\n<meta charset=\\\"utf-8\\\">\\n<title>Error</title>\\n</head>\\n<body>\\n<pre>Bad Request</pre>\\n</body>\\n</html>\\n\"}', '2026-08-13 20:35:09'),
(3, 'OUTBOUND', NULL, '628114560234', '6287854710790', NULL, 'text', 'HALOOOOOOO', 'FAILED', 400, '{\"raw_response\": \"<!DOCTYPE html>\\n<html lang=\\\"en\\\">\\n<head>\\n<meta charset=\\\"utf-8\\\">\\n<title>Error</title>\\n</head>\\n<body>\\n<pre>Bad Request</pre>\\n</body>\\n</html>\\n\"}', '2026-08-13 20:39:18'),
(4, 'OUTBOUND', NULL, '628114560234', '6287854710790', NULL, 'text', 'Halooo Maseh', 'FAILED', 400, '{\"raw_response\": \"<!DOCTYPE html>\\n<html lang=\\\"en\\\">\\n<head>\\n<meta charset=\\\"utf-8\\\">\\n<title>Error</title>\\n</head>\\n<body>\\n<pre>Bad Request</pre>\\n</body>\\n</html>\\n\"}', '2026-08-13 20:39:59'),
(5, 'OUTBOUND', NULL, '628114560234', '6287854710790', NULL, 'text', 'Halo Maseh', 'FAILED', 400, '{\"raw_response\": \"<!DOCTYPE html>\\n<html lang=\\\"en\\\">\\n<head>\\n<meta charset=\\\"utf-8\\\">\\n<title>Error</title>\\n</head>\\n<body>\\n<pre>Bad Request</pre>\\n</body>\\n</html>\\n\"}', '2026-08-13 20:41:04'),
(6, 'OUTBOUND', NULL, '628114560234', '6287854710790', NULL, 'text', 'HALOOO MASEEEHHH', 'FAILED', 400, '{\"raw_response\": \"<!DOCTYPE html>\\n<html lang=\\\"en\\\">\\n<head>\\n<meta charset=\\\"utf-8\\\">\\n<title>Error</title>\\n</head>\\n<body>\\n<pre>Bad Request</pre>\\n</body>\\n</html>\\n\"}', '2026-08-13 20:43:18'),
(7, 'OUTBOUND', NULL, '628114560234', '6287854710790', NULL, 'text', 'HALO TESTING', 'SUCCESS', 200, '{\"status\": true, \"msg\": \"Message sent successfully to 6287854710790@s.whatsapp.net\"}', '2026-08-13 20:55:09'),
(8, 'INBOUND', NULL, NULL, NULL, NULL, 'unknown', NULL, 'RECEIVED', 200, '{\"raw\": \"\"}', '2026-08-13 20:55:31'),
(9, 'INBOUND', NULL, NULL, NULL, NULL, 'unknown', NULL, 'RECEIVED', 200, '{\"raw\": \"\"}', '2026-08-13 20:55:36'),
(10, 'INBOUND', NULL, '628114560234', NULL, 'Albert', 'message', 'Uhuy', 'RECEIVED', 200, '{\"type\": \"message\", \"messageType\": \"text\", \"from\": \"6287854710790\", \"sender_jid\": \"196872761249990@lid\", \"isGroup\": false, \"sender\": \"628114560234\", \"pushName\": \"Albert\", \"timestamp\": \"2026-08-13T14:10:26.740Z\", \"body\": \"Uhuy\", \"hasMedia\": false, \"fileUrl\": null, \"mimetype\": null, \"mediaType\": null, \"fileName\": null}', '2026-08-13 21:10:26'),
(11, 'INBOUND', NULL, '628114560234', NULL, 'Albert', 'message', 'Uhuy', 'RECEIVED', 200, '{\"type\": \"message\", \"messageType\": \"text\", \"from\": \"6287854710790\", \"sender_jid\": \"196872761249990@lid\", \"isGroup\": false, \"sender\": \"628114560234\", \"pushName\": \"Albert\", \"timestamp\": \"2026-08-13T14:12:09.908Z\", \"body\": \"Uhuy\", \"hasMedia\": false, \"fileUrl\": null, \"mimetype\": null, \"mediaType\": null, \"fileName\": null}', '2026-08-13 21:12:10'),
(12, 'INBOUND', NULL, '628114560234', '628114560234', 'Albert', 'message', 'Loha', 'RECEIVED', 200, '{\"type\": \"message\", \"messageType\": \"text\", \"from\": \"6287854710790\", \"sender_jid\": \"196872761249990@lid\", \"isGroup\": false, \"sender\": \"628114560234\", \"pushName\": \"Albert\", \"timestamp\": \"2026-08-13T14:13:31.393Z\", \"body\": \"Loha\", \"hasMedia\": false, \"fileUrl\": null, \"mimetype\": null, \"mediaType\": null, \"fileName\": null}', '2026-08-13 21:13:31'),
(13, 'INBOUND', NULL, '628114560234', '628114560234', 'Albert', 'message', 'Halo', 'RECEIVED', 200, '{\"type\": \"message\", \"messageType\": \"text\", \"from\": \"6287854710790\", \"sender_jid\": \"196872761249990@lid\", \"isGroup\": false, \"sender\": \"628114560234\", \"pushName\": \"Albert\", \"timestamp\": \"2026-08-13T14:16:14.879Z\", \"body\": \"Halo\", \"hasMedia\": false, \"fileUrl\": null, \"mimetype\": null, \"mediaType\": null, \"fileName\": null}', '2026-08-13 21:16:15'),
(14, 'INBOUND', NULL, '628114560234', '6287854710790', 'Albert', 'text', 'Loh jgn di read kk omg', 'RECEIVED', 200, '{\"type\": \"message\", \"messageType\": \"text\", \"from\": \"6287854710790\", \"sender_jid\": \"196872761249990@lid\", \"isGroup\": false, \"sender\": \"628114560234\", \"pushName\": \"Albert\", \"timestamp\": \"2026-08-13T14:19:42.769Z\", \"body\": \"Loh jgn di read kk omg\", \"hasMedia\": false, \"fileUrl\": null, \"mimetype\": null, \"mediaType\": null, \"fileName\": null}', '2026-08-13 21:19:42'),
(15, 'INBOUND', NULL, '628114560234', '6287854710790', 'Albert', 'text', '🙂', 'RECEIVED', 200, '{\"type\": \"message\", \"messageType\": \"text\", \"from\": \"6287854710790\", \"sender_jid\": \"196872761249990@lid\", \"isGroup\": false, \"sender\": \"628114560234\", \"pushName\": \"Albert\", \"timestamp\": \"2026-08-13T14:22:57.334Z\", \"body\": \"🙂\", \"hasMedia\": false, \"fileUrl\": null, \"mimetype\": null, \"mediaType\": null, \"fileName\": null}', '2026-08-13 21:22:57'),
(16, 'INBOUND', NULL, '628114560234', '6287854710790', 'Albert', 'text', 'Test 🙂', 'RECEIVED', 200, '{\"type\": \"message\", \"messageType\": \"text\", \"from\": \"6287854710790\", \"sender_jid\": \"196872761249990@lid\", \"isGroup\": false, \"sender\": \"628114560234\", \"pushName\": \"Albert\", \"timestamp\": \"2026-08-13T14:23:12.243Z\", \"body\": \"Test 🙂\", \"hasMedia\": false, \"fileUrl\": null, \"mimetype\": null, \"mediaType\": null, \"fileName\": null}', '2026-08-13 21:23:12'),
(17, 'OUTBOUND', NULL, '628114560234', '6287854710790', NULL, 'text', 'HALOOO', 'SUCCESS', 200, '{\"status\": true, \"msg\": \"Message sent successfully to 6287854710790@s.whatsapp.net\"}', '2026-08-13 21:23:51'),
(18, 'OUTBOUND', NULL, '628114560234', '6287854710790', NULL, 'text', 'Testing haloo', 'SUCCESS', 200, '{\"status\": true, \"msg\": \"Message sent successfully to 6287854710790@s.whatsapp.net\"}', '2026-08-13 21:26:24'),
(19, 'INBOUND', NULL, '628114560234', '6287854710790', 'Albert', 'text', 'Mantab', 'RECEIVED', 200, '{\"type\": \"message\", \"messageType\": \"text\", \"from\": \"6287854710790\", \"sender_jid\": \"196872761249990@lid\", \"isGroup\": false, \"sender\": \"628114560234\", \"pushName\": \"Albert\", \"timestamp\": \"2026-08-13T14:26:34.444Z\", \"body\": \"Mantab\", \"hasMedia\": false, \"fileUrl\": null, \"mimetype\": null, \"mediaType\": null, \"fileName\": null}', '2026-08-13 21:26:34');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `whatsapp_messages`
--
ALTER TABLE `whatsapp_messages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_direction` (`direction`),
  ADD KEY `idx_sender` (`sender`),
  ADD KEY `idx_receiver` (`receiver`),
  ADD KEY `idx_created_at` (`created_at`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `whatsapp_messages`
--
ALTER TABLE `whatsapp_messages`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
