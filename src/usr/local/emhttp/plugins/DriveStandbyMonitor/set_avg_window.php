<?
libxml_use_internal_errors(true);
$scriptName = "DriveStandbyMonitor";
$docroot = $docroot ?? $_SERVER['DOCUMENT_ROOT'] ?: '/usr/local/emhttp';

$allowedWindows = array(1,3,7,14,30,90,365);
$days = isset($_GET['days']) ? intval($_GET['days']) : 30;
if (!in_array($days, $allowedWindows)) $days = 30;

$cfgFile = "/boot/config/plugins/DriveStandbyMonitor/settings.cfg";
@mkdir(dirname($cfgFile), 0777, true);

// read existing
$settings = @parse_ini_file($cfgFile) ?: [];
$settings['AVG_WINDOW_DAYS'] = $days;

// write back
$lines = "";
foreach ($settings as $k => $v) {
    // keep it simple; numeric values only currently
    $lines .= $k . "=\"" . $v . "\"\n";
}
file_put_contents($cfgFile, $lines);

header('Content-Type: application/json');
echo json_encode(array('ok' => true, 'AVG_WINDOW_DAYS' => $days));
?>
