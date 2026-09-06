<?php
// check + disable browser-trigger archiving option
mysqli_report(MYSQLI_REPORT_OFF);
$c = @new mysqli('127.0.0.1', 'matomo', 'matomo', 'matomo', 3307);
if ($c->connect_error) { die('ERR ' . $c->connect_error . PHP_EOL); }
$r = $c->query("SELECT option_value FROM matomo_option WHERE option_name='enableBrowserTriggerArchiving'");
if ($r && $row = $r->fetch_assoc()) {
    echo 'option enableBrowserTriggerArchiving = ' . $row['option_value'] . PHP_EOL;
    $c->query("UPDATE matomo_option SET option_value='0' WHERE option_name='enableBrowserTriggerArchiving'");
    echo 'set to 0' . PHP_EOL;
} else {
    echo 'option not present (config fallback used)' . PHP_EOL;
}
