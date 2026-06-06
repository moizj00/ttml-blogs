# TTML Blog Master — daily self-learning blog reviewer.
# Runs the `claude` CLI headless once a day, critiques live posts against the
# vault's craft standards, appends remarks to .claude/memory.md, commits + pushes.
FROM node:22-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates tini coreutils \
 && rm -rf /var/lib/apt/lists/* \
 && npm install -g @anthropic-ai/claude-code

WORKDIR /opt/blog-master
COPY review-prompt.md entrypoint.sh loop.sh ./
RUN chmod +x entrypoint.sh loop.sh

ENV WORKDIR=/work/repo \
    BLOG_REPO=moizj00/ttml-blogs \
    BLOG_BRANCH=master \
    DAILY_UTC_HOUR=13 \
    RUN_ON_START=false

VOLUME ["/work"]
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["/opt/blog-master/loop.sh"]
