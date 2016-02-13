#!/bin/bash

# This script should be run from within an extracted tarball created by
# package.sh in this directory. Its purpose is to automate the process of
# deploying a new test tarball on a ops/manufacter laptop.
#
# Initial setup of test execution dependencies is currently out of scope.
# Also out of scope for now is getting the tarball extracted.

set -e
set -u

DIR=$(dirname "$0")

: ${DEPLOY_ROOT:="$HOME"}
: ${LINKS_ROOT:="${DEPLOY_ROOT}/Desktop"}
# This nasty hack is because realpath doesn't exist on OSX.
: ${PACKAGE_ROOT:=$(echo 'import os; print os.path.realpath("${DIR}/..")' | python2.7)}

package_name=$(basename "${PACKAGE_ROOT}")

if [ -f sha1sums.txt ]; then
  echo 'Checking package integrity...'
  sha1sum -c sha1sums.txt
fi

cd "${PACKAGE_ROOT}/.."

dest_dir="${DEPLOY_ROOT}/${package_name}"
versioned_dir="${DEPLOY_ROOT}/major-tom-versions/${package_name}"
log_dir="${DEPLOY_ROOT}/major-tom-test-logs/${package_name}"

mkdir -p "${versioned_dir}"
mkdir -p "${log_dir}"

# Install test packages if they exist.
if [ -d "${PACKAGE_ROOT}/deps/pip" ]; then
  pip_build_tmp=$(mktemp -d /tmp/tmp.loon.XXXXX)
  declare -a test_packages
  for pip_file in $(ls "${PACKAGE_ROOT}/deps/pip")
  do
    test_packages+=("${PACKAGE_ROOT}/deps/pip/${pip_file}")
  done
  sudo pip install --build="$pip_build_tmp" "${test_packages[@]}"
  rm -rf $pip_build_tmp
fi

# Move the package directory to the archive directory only if the package
# directory is not already in the archive directory.
if [ ! "${PACKAGE_ROOT}" -ef "${versioned_dir}" ]; then
  # If we already have a copy of this version, delete it
  rm -rf "${versioned_dir}"

  # Move package to archive directory
  mv "${PACKAGE_ROOT}" "${versioned_dir}"
fi

# Remove old test directory symlink
find ${DEPLOY_ROOT} -maxdepth 1 -type l -name "major-tom-*" -exec rm {} \;

# Symlink test directory to archive directory
ln -sf "${versioned_dir}" "${dest_dir}"

# Symlink test log directory to central test log directory
rm -rf "${versioned_dir}/test_logs"
ln -sf ${log_dir} "${versioned_dir}/test_logs"

echo "Done!"
