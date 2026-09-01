<?
libxml_use_internal_errors(true);
$scriptName = "DriveStandbyMonitor";
$docroot = $docroot ?? $_SERVER['DOCUMENT_ROOT'] ?: '/usr/local/emhttp';

$cfgFile = "/boot/config/plugins/DriveStandbyMonitor/settings.cfg";
@mkdir(dirname($cfgFile), 0777, true);

// Parse selected drives from query parameter
$drivesParam = isset($_GET['drives']) ? $_GET['drives'] : '';
$drives = [];
if ($drivesParam !== '') {
    foreach (explode(',', $drivesParam) as $d) {
        $d = trim($d);
        if ($d !== '') $drives[] = $d;
    }
}

// read existing settings
$settings = @parse_ini_file($cfgFile) ?: [];
$settings['MAIN_VISIBLE_DRIVES'] = implode(',', $drives);

// write back
$lines = "";
foreach ($settings as $k => $v) {
    $lines .= $k . "=\"" . $v . "\"\n";
}
file_put_contents($cfgFile, $lines);

header('Content-Type: application/json');
echo json_encode(array('ok' => true, 'MAIN_VISIBLE_DRIVES' => $settings['MAIN_VISIBLE_DRIVES']));
?>
