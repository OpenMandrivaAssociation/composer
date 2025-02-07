#!/bin/bash

NAME=$(sed    -n '/^Name:/{s/.* //;p}'                  *.spec)
OWNER=$(sed   -n '/^%global gh_owner/{s/.* //;p}'   $NAME.spec)
PROJECT=$(sed -n '/^%global gh_project/{s/.* //;p}' $NAME.spec)
VERSION=$(sed -n '/^%global upstream_version/{s/.* //;p}' $NAME.spec)
PREVER=$(sed -n '/^%global upstream_prever/{s/.* //;p}' $NAME.spec)
COMMIT=$(sed  -n '/^%global gh_commit/{s/.* //;p}'  $NAME.spec)
SHORT=${COMMIT:0:7}

if [ -f $NAME-$VERSION$PREVER-$SHORT.tgz -a "$1" != "-f" ]; then
	echo skip $NAME-$VERSION$PREVER-$SHORT.tgz already here
else
	echo -e "\nCreate git snapshot\nName=$NAME, Owner=$OWNER, Project=$PROJECT, Version=$VERSION$PREVER\n"

	echo "Cloning..."
	git clone https://github.com/$OWNER/$PROJECT.git $PROJECT-$COMMIT

	echo "Getting commit..."
	pushd $PROJECT-$COMMIT
		git checkout $COMMIT || exit 1
		cp composer.json ../composer.json
		composer config platform.php 7.2.5
		rm composer.lock
		composer install --no-interaction --no-progress --no-dev --optimize-autoloader
		cp vendor/composer/installed.json ../
		# bash completion
		bin/composer completion bash >../composer-bash-completion
	popd

	echo "Archiving..."
	tar czf $NAME-$VERSION$PREVER-$SHORT.tgz --exclude .git $PROJECT-$COMMIT

	echo "Cleaning..."
	rm -rf $PROJECT-$COMMIT
fi
echo "Done."
