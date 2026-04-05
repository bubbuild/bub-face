---
name: emotion
description: Use this when you want to change the emotion of the robo eyes.
---

# Bub Face Emotion Skill

To change the emotion of the face, run:

```
curl -X POST http://localhost:28282/api/emotion -H "Content-Type: application/json" -d '{"emotion": "happy"}'
```

If the API returns 200 with the correct emotion in state, it means the emotion has been successfully updated.

**Available emotions:**

- neutral
- happy
- sad
- angry
- surprised
- curious
- sleepy
- love
- thinking
