<?php
// quick DB stats query
mysqli_report(MYSQLI_REPORT_OFF);
$c = @new mysqli('127.0.0.1', 'matomo', 'matomo', 'matomo', 3307);
if ($c->connect_error) { die('ERR ' . $c->connect_error . PHP_EOL); }
foreach (['matomo_log_visit', 'matomo_log_conversion', 'matomo_log_link_visit_action'] as $t) {
    $r = $c->query('SELECT COUNT(*) c FROM ' . $t);
    $row = $r->fetch_assoc();
    echo $t . ' = ' . $row['c'] . PHP_EOL;
}
$r = $c->query('SELECT idsite, COUNT(*) c FROM matomo_log_visit GROUP BY idsite');
while ($row = $r->fetch_assoc()) {
    echo 'visit idsite=' . $row['idsite'] . ' c=' . $row['c'] . PHP_EOL;
}
