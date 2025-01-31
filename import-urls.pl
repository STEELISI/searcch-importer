# Specify the file which has URLs to import and the file showing
# what was imported up to now. Then invoke importer to
# import everything
use Digest::MD5 qw(md5_hex);
use POSIX qw(strftime);

$usage = "$0 new-file imported-objects log-path\n";

if ($#ARGV < 2)
{
    print $usage;
    exit 0;
}
%imported = ();
my $fh = new IO::File($ARGV[1]);
while(<$fh>)
{
    $_ =~ s/\s+//g;
    $imported{$_} = 0;
}
close($fh);
@toimport = ();
my $fh = new IO::File($ARGV[0]);
while(<$fh>)
{	
    $_ =~ s/\s+//g;
    if (!exists($imported{$_}))
    {			      
	push(@toimport, $_);
    }
}
for $u (@toimport)
{
	print "Will import $u\n";
}
$myscript = "";

for $i (@toimport)
{
        $myscript .= "bash import-and-publish $i\n";
}
$myscript .= "searcch-importer artifact.export -a -e searcch\n";
open (my $oh, '>', $ARGV[2] . '/logs/importer-script.sh');
print $oh $myscript;
close($oh);
print "$myscript\n";
print "Printed into $ARGV[2]/logs/importer-script.sh\n";
system("docker compose down");
system("docker compose up -d searcch-importer-prod");
sleep(10);
system("docker exec -i searcch-importer-prod /bin/sh -c \"bash logs/importer-script.sh\" | grep Exported > exported.txt");
system("docker exec -i searcch-importer-prod /bin/sh -c \"searcch-importer artifact.list -all\" >> nowimported.txt");
my $fh = new IO::File("nowimported.txt");
%importednow = ();
while(<$fh>)
{
    @items = split /\,/, $_;
    @elems = split /\=/, $items[0];
    my $id = $elems[1];
    @elems = split /\=/, $items[2];
    my $url = $elems[1];
    $url =~ s/\'//g;
    $importednow{$id} = $url;
    print "Now imported $url ID $id\n";
}
close($fh);
my $fh = new IO::File("exported.txt");
while(<$fh>)
{
    @items = split /\,/, $_;
    @elems = split /\=/, $items[0];
    my $id = $elems[1];
    $imported{$importednow{$id}} = 1;
    print "Successfully exported $importednow{$id}\n";
}
close($fh);
open (my $oh, '>', 'imported.txt');
for $i (keys %imported)
{
    print $oh "$i\n";
}
close($oh);


