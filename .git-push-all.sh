#!/bin/bash
# Push to both GitHub and GitLab simultaneously

echo "🚀 Pushing to all remotes..."

git push origin master &
PID1=$!

git push gitlab master &
PID2=$!

wait $PID1
RESULT1=$?

wait $PID2
RESULT2=$?

if [ $RESULT1 -eq 0 ] && [ $RESULT2 -eq 0 ]; then
    echo "✅ Successfully pushed to both GitHub and GitLab!"
elif [ $RESULT1 -eq 0 ]; then
    echo "⚠️  GitHub: ✅  |  GitLab: ❌"
    exit 1
elif [ $RESULT2 -eq 0 ]; then
    echo "⚠️  GitHub: ❌  |  GitLab: ✅"
    exit 1
else
    echo "❌ Failed to push to both remotes"
    exit 1
fi
