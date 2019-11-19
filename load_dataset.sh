
mkdir -p ./data

echo "Downloading paracrawl v5 en-de."
# curl https://s3.amazonaws.com/web-language-models/paracrawl/release5/en-de.classify.gz  > ./data/en-de.gz 
curl https://s3.amazonaws.com/web-language-models/paracrawl/release5/en-de.bicleaner07.tmx.gz > ./data/en-de.bicleaner07.tmx.gz
# curl https://s3.amazonaws.com/web-language-models/paracrawl/release5/en-de.bicleaner07.txt.gz > ./data/en-de.bicleaner07.txt.gz 

echo "Extracting paracrawl v5 en-de."
gunzip -zxvf ./data/en-de.bicleaner07.tmx.gz
# tar -zxvf ./data/en-de.bicleaner07.txt.gz