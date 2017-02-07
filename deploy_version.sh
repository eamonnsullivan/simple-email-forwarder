#!/bin/sh

profile='home'
function_name='svpEmailHandler'
zip_file='SimpleForwarder.zip'
code_file='SimpleForwarder.py'

# Zip code
zip $zip_file $code_file

# update code on lambda
aws --profile $profile lambda update-function-code --function-name $function_name --zip-file fileb://$zip_file --publish 

# remove the zip file
rm $zip_file
