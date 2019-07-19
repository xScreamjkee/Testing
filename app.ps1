$COMMIT_MSG=(git rev-parse HEAD)
$COMMIT_MSG #="1f6398a60f7500eb4b9a4c59d4f8032727996db4"
#$last_msg="1f6398a60f7500eb4b9a4c59d4f8032727996db2"
#if ($COMMIT_MSG -ge $last_msg) {
#	echo "No update commits"
#}

#if ($COMMIT_MSG -ne $last_msg) {
#	echo "Commit update"
#	$last_msg=$COMMIT_MSG
#	echo $last_msg
#}

#$test=(git diff-index --quiet HEAD --)
#if ($test)
#{ 
#   echo "$test - No changes"
#}
#else{
#    echo "$test - Changes"
#}


git fetch
$base=(git rev-parse HEAD)
$new=(git rev-parse @{u})
if ($base == $new)
{
	echo "No changes"
}

else
{
	echo "Updated"
}