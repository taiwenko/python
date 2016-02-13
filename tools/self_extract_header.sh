#!/bin/bash

# When a distribution package is base64 encoded and appended to this file, it
# becomes a self-extracting and installing archive. Great for setting up and
# upgrading manufacturing and operations tests.

set -e
set -u

export temp_dir=$(mktemp -d /tmp/mtp-tmp.XXXXXXXXXX)

# The decoded major tom package
tar_file=$temp_dir/mt-package

# The checksum for the major tom package
check_file=$temp_dir/checksum

# Find where the package data begins
archive_line=`awk '/^__ARCHIVE_BELOW__/ {print NR + 1; exit 0;}' "$0"`

# Remove and decode the data. The arguments differ between Linux and OSX
unamestr=`uname`
decode_flag=""
if [[ $unamestr == "Linux" ]]; then
  decode_flag="-d"
elif [[ $unamestr == "Darwin" ]]; then
  decode_flag="-D"
else
  echo "Unsupported platform: $unamestr"
  exit 1
fi

tail -n+$archive_line "$0" | base64 $decode_flag > ${tar_file}

# Extract the checksum
sha_line=$(grep '^__ARCHIVE_BELOW__: sha1sum ' "$0")
if [ $? == 0 ]; then
  # Verify the checksum
  tar_checksum=$(echo "${sha_line}" | cut -f 3 -d ' ')
  # sha1sum requires two spaces between the checksum and the file name.
  echo "${tar_checksum}  ${tar_file}" > ${check_file}
  sha1sum -c ${check_file}
  if [ $? != 0 ]; then
    echo "Checksum failed. Please redownload."
    exit 1
  fi
else
  echo "Checksum not found. Please redownload."
  exit 1
fi

# Extract and deploy
tar xf ${tar_file} --directory ${temp_dir}
cd "$(find ${temp_dir} -maxdepth 1 -type d -name '${_PACKAGE_NAME}*')"
chmod +x tools/deploy_me.sh
tools/deploy_me.sh

read -p "Press Enter to continue..."
exit 0
