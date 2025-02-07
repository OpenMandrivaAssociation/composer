%global gh_commit    ae208dc1e182bd45d99fcecb956501da212454a1
%global gh_short     %(c=%{gh_commit}; echo ${c:0:7})
%global gh_branch    2.0-dev
%global api_version  2.6.0
%global run_version  2.2.2

%global _phpunit       %{_bindir}/phpunit9
%global bashcompdir    %(pkg-config --variable=completionsdir bash-completion 2>/dev/null)
%global bashcomproot   %(dirname %{bashcompdir} 2>/dev/null)

Name:           composer
Version:        2.8.5
Release:        1
Summary:        Dependency Manager for PHP
License:        MIT
URL:            https://getcomposer.org/
Source0:        composer-%{version}-%{gh_short}.tgz
# Profile scripts
Source1:        %{name}-bash-completion
Source3:        %{name}.sh
Source4:        %{name}.csh
# Create a git snapshot with dependencies
Source5:        makesrc.sh
# Use our autoloader, resources path, fix for tests
Patch0:         %{name}-rpm.patch
# Disable XDG support as only partially implemented
Patch1:         %{name}-noxdg.patch
BuildArch:      noarch
# platform set in makesrc.sh
BuildRequires:  php-cli
BuildRequires:  pkgconfig(bash-completion)

Requires:       php-cli
# System certificates
Requires:       ca-certificates

# From composer.json, suggest
#        "ext-openssl": "Enabling the openssl extension allows you to access https URLs for repositories and packages",
#        "ext-zip": "Enabling the zip extension allows you to unzip archives",
#        "ext-zlib": "Allow gzip compression of HTTP requests"
Requires:       php-openssl
Requires:       php-zip
Requires:       php-zlib
Requires:       php-ctype
Requires:       php-curl
Requires:       php-phar

# Special internal for Plugin API
Provides:       php-composer(composer-plugin-api) = %{api_version}
Provides:       php-composer(composer-runtime-api) = %{run_version}


%description
Composer helps you declare, manage and install dependencies of PHP projects,
ensuring you have the right stack everywhere.

Documentation: https://getcomposer.org/doc/


%prep
%setup -q -n composer-%{gh_commit}

%patch -P0 -p1 -b .rpm
%patch -P1 -p1 -b .noxdg
find . \( -name \*.rpm -o -name \*noxdg \) -delete -print

rm vendor/composer/ca-bundle/res/cacert.pem

: List bundled libraries and Licenses
php -r '
	$pkgs = file_get_contents("vendor/composer/installed.json");
	$pkgs = json_decode($pkgs, true);
	if (!is_array($pkgs) || !isset($pkgs["packages"])) {
        echo "cant decode json file\n";
		exit(3);
	}
	$res = [];
    foreach($pkgs["packages"] as $pkg) {
		$lic = implode(" and ", $pkg["license"]);
		if (!isset($res[$lic])) $res[$lic] = [];
		$res[$lic][] = sprintf("Provides:       bundled(php-composer(%s)) = %s", $pkg["name"], trim($pkg["version"], "v"));
	}
	foreach($res as $lic => $lib) {
		sort($lib);
		printf("# License %s\n%s\n", $lic, implode("\n", $lib));
	}
'

: fix reported version
sed -e '/BRANCH_ALIAS_VERSION/s/@package_branch_alias_version@//' \
    -i src/Composer/Composer.php

: check Plugin API version
php -r '
namespace Composer;
include "src/bootstrap.php";
if (version_compare(Plugin\PluginInterface::PLUGIN_API_VERSION, "%{api_version}")) {
  printf("Plugin API version is %s, expected %s\n", Plugin\PluginInterface::PLUGIN_API_VERSION, "%{api_version}");
  exit(1);
}
if (version_compare(Composer::RUNTIME_API_VERSION, "%{run_version}")) {
  printf("Runtime API version is %s, expected %s\n", Composer::RUNTIME_API_VERSION, "%{run_version}");
  exit(1);
}'


%build
: Nothing to build


%install
: Profile scripts
install -Dpm 644 %{SOURCE1} %{buildroot}%{bashcompdir}/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/profile.d
install -m 644 %{SOURCE3} %{SOURCE4} %{buildroot}%{_sysconfdir}/profile.d/

: Library autoloader for compatibility
mkdir -p     %{buildroot}%{_datadir}/php/Composer
ln -s ../../composer/vendor/autoload.php %{buildroot}%{_datadir}/php/Composer/autoload.php

: Sources
mkdir -p %{buildroot}%{_datadir}/%{name}
cp -pr src res vendor LICENSE\
         %{buildroot}%{_datadir}/%{name}/

: Command
install -Dpm 755 bin/%{name} %{buildroot}%{_bindir}/%{name}

: Licenses
ln -sf ../../%{name}/LICENSE LICENSE
cd vendor
for lic in */*/LICENSE
do dir=$(dirname $lic)
   own=$(dirname $dir)
   prj=$(basename $dir)
   ln -sf ../../composer/vendor/$own/$prj/LICENSE ../$own-$prj-LICENSE
done


%check
: Check autoloader
php -r '
  include "%{buildroot}%{_datadir}/%{name}/src/bootstrap.php";
  exit (class_exists("Composer\\Composer") ? 0 : 1);
'
: Check compatibility autoloader
php -r '
  include "%{buildroot}%{_datadir}/php/Composer/autoload.php";
  exit (class_exists("Composer\\Composer") ? 0 : 2);
'


%files
%license *LICENSE
%doc *.md
%doc doc
%doc composer.json
%config(noreplace) %{_sysconfdir}/profile.d/%{name}.*
%{_bindir}/%{name}
%{_datadir}/php/Composer
%{_datadir}/%{name}
%{bashcomproot}
