-- Skapa emails-tabell om den inte finns
CREATE TABLE IF NOT EXISTS emails (
  id VARCHAR(36) PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  date DATETIME NOT NULL,
  preview TEXT,
  count VARCHAR(50),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Skapa schedules-tabell om den inte finns
CREATE TABLE IF NOT EXISTS schedules (
  id VARCHAR(36) PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  subtitle VARCHAR(255),
  status VARCHAR(50) NOT NULL,
  date_type VARCHAR(50) NOT NULL COMMENT 'publishing eller recalling',
  trigger_date DATETIME NOT NULL,
  delay_type VARCHAR(50) NOT NULL COMMENT 'before eller after',
  delay_days INT NOT NULL,
  email_template VARCHAR(255) NOT NULL,
  recipients JSON COMMENT 'Array med mottagartyper (guest, team, host)',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  next_run DATETIME
);

-- Lägg till exempeldata i emails-tabellen
INSERT INTO emails (id, title, date, preview, count) VALUES
(UUID(), 'Välkommen till The Authority Show', NOW(), 'Vi ser fram emot att ha dig som gäst...', '3'),
(UUID(), 'Förberedelser inför inspelning', DATE_ADD(NOW(), INTERVAL -2 DAY), 'Här är några tips inför din medverkan...', '1'),
(UUID(), 'Tack för din medverkan', DATE_ADD(NOW(), INTERVAL -7 DAY), 'Vi vill tacka dig för din medverkan i The Authority Show...', '5');

