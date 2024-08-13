#!/bin/zsh


function commit {
  set -e
  echo "enter commit msg: "
  read -r msg

  echo "Current status: "
  git status
  echo "Press enter to accept all these changes, otherwise enter files to stage for commit: "
  read -r accept_type

  if [ "${accept_type}" != "" ]; then
    git add "${accept_type}"
  else
    git add --all
  fi

  git commit -m "${msg}"
  git push origin
}

commit



