#!/bin/bash
set -e

# List of image/tags to keep (separated by "|")
WHITELIST_REGEX="freecad-automation-macro|ubuntu:22.04"

# Enable dry-run mode (set to "true" to simulate, "false" to actually delete)
DRY_RUN="false" # Set to "true" for a test run without actual deletion

echo "🧹 Starting Docker cleanup with whitelist: $WHITELIST_REGEX"

if [ "$DRY_RUN" = "true" ]; then
  echo "--- DRY RUN MODE ENABLED --- No actual deletions will occur."
fi

echo "🗑️ Pruning exited containers..."
if [ "$DRY_RUN" = "true" ]; then
  echo "  (Dry Run) docker container prune -f"
else
  docker container prune -f
fi

echo "🗑️ Pruning build cache..."
if [ "$DRY_RUN" = "true" ]; then
  echo "  (Dry Run) docker builder prune -f"
else
  docker builder prune -f
fi

echo "🗑️ Pruning unused volumes..."
if [ "$DRY_RUN" = "true" ]; then
  echo "  (Dry Run) docker volume prune -f"
else
  docker volume prune -f
fi

echo "🗑️ Pruning unused networks..."
if [ "$DRY_RUN" = "true" ]; then
  echo "  (Dry Run) docker network prune -f"
else
  docker network prune -f
fi

echo "🔍 Deleting unused images not in whitelist..."

docker images --format "{{.Repository}}:{{.Tag}} {{.ID}}" | while read -r line; do
  image_tag=$(cut -d' ' -f1 <<< "$line")
  image_id=$(cut -d' ' -f2 <<< "$line")

  if [[ "$image_tag" =~ $WHITELIST_REGEX ]]; then
    echo "✅ Keeping: $image_tag"
  else
    echo "🗑️ Deleting image: $image_tag ($image_id)"
    if [ "$DRY_RUN" = "true" ]; then
      echo "  (Dry Run) docker rmi -f \"$image_id\""
    else
      docker rmi -f "$image_id" || true
    fi
  fi
done

echo "📊 After cleanup:"
docker system df

echo "✅ Cleanup complete!"