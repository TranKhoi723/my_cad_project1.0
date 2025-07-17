#!/bin/bash
set -e

# Danh sách image/tag cần giữ lại (cách nhau bởi dấu "|")
WHITELIST_REGEX="freecad-automation-macro|ubuntu:22.04"

echo "🧹 Bắt đầu dọn dẹp Docker với whitelist: $WHITELIST_REGEX"

echo "🗑️ Dọn container đã thoát..."
docker container prune -f

echo "🗑️ Dọn build cache..."
docker builder prune -f

echo "🗑️ Dọn volumes không dùng..."
docker volume prune -f

echo "🔍 Xoá image không dùng và không nằm trong whitelist..."

docker images --format "{{.Repository}}:{{.Tag}} {{.ID}}" | while read -r line; do
  image_tag=$(cut -d' ' -f1 <<< "$line")
  image_id=$(cut -d' ' -f2 <<< "$line")

  if [[ "$image_tag" =~ $WHITELIST_REGEX ]]; then
    echo "✅ Giữ lại: $image_tag"
  else
    echo "🗑️ Xoá image: $image_tag ($image_id)"
    docker rmi -f "$image_id" || true
  fi
done

echo "📊 Sau khi dọn dẹp:"
docker system df

echo "✅ Hoàn tất!"
