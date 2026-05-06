#!/bin/bash
# Quick test of AOT daemons

echo "=== Testing SynanDaemon (morphology) ==="
curl -s -G --data-urlencode "action=morph" --data-urlencode "langua=Russian" --data-urlencode "query=машина" "http://127.0.0.1:8082/" | python3 -m json.tool 2>/dev/null || curl -s -G --data-urlencode "action=morph" --data-urlencode "langua=Russian" --data-urlencode "query=машина" "http://127.0.0.1:8082/"

echo -e "\n\n=== Testing SynanDaemon (syntax) ==="
curl -s -G --data-urlencode "action=syntax" --data-urlencode "langua=Russian" --data-urlencode "query=Я иду домой" "http://127.0.0.1:8082/" | head -c 500

echo -e "\n\n=== Testing SemanDaemon (translate) ==="
curl -s -G --data-urlencode "action=translate" --data-urlencode "langua=Russian" --data-urlencode "query=Мама мыла раму" --data-urlencode "topic=common" "http://127.0.0.1:8081/"

echo -e "\n\n=== Testing SemanDaemon (graph) ==="
curl -s -G --data-urlencode "action=graph" --data-urlencode "langua=Russian" --data-urlencode "query=Мама мыла раму" --data-urlencode "topic=common" "http://127.0.0.1:8081/" | python3 -m json.tool 2>/dev/null | head -30

echo -e "\n\n=== Done ==="
