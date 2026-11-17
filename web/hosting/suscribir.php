<?php
// Boletín de {{NOMBRE_LARGO}}: guarda cada correo en boletin_privado/suscriptores.csv, fuera de la carpeta pública si se puede.
header('Content-Type: application/json; charset=utf-8');
header('X-Robots-Tag: noindex');
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo '{"ok":false}'; exit; }
if (!empty($_POST['bot-field'])) { echo '{"ok":true}'; exit; }
$email = trim(isset($_POST['email']) ? $_POST['email'] : '');
if (strlen($email) > 254 || !filter_var($email, FILTER_VALIDATE_EMAIL)) { http_response_code(400); echo '{"ok":false}'; exit; }
$dir = dirname(__DIR__) . '/boletin_privado';
if (!is_dir($dir)) { @mkdir($dir, 0700, true); }
if (!file_exists($dir . '/.htaccess')) { @file_put_contents($dir . '/.htaccess', "Require all denied\nDeny from all\n"); }
$line = gmdate('c') . ',' . str_replace(array(',', "\n", "\r"), '', $email) . "\n";
$ok = @file_put_contents($dir . '/suscriptores.csv', $line, FILE_APPEND | LOCK_EX);
echo json_encode(array('ok' => $ok !== false));
