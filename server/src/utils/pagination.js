const DEFAULT_LIMIT = 20;
const MAX_LIMIT = 100;

function parseLimit(value, fallback = DEFAULT_LIMIT) {
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed) || parsed < 1) return fallback;
  return Math.min(parsed, MAX_LIMIT);
}

function encodeCursor(value) {
  if (!value) return null;
  return Buffer.from(String(value), 'utf8').toString('base64url');
}

function decodeCursor(cursor) {
  if (!cursor) return null;
  try {
    return Buffer.from(cursor, 'base64url').toString('utf8');
  } catch {
    return null;
  }
}

function pageResult(rows, limit, cursorField = 'created_at') {
  const hasMore = rows.length > limit;
  const data = hasMore ? rows.slice(0, limit) : rows;
  const last = data[data.length - 1];

  return {
    data,
    nextCursor: hasMore && last ? encodeCursor(last[cursorField]) : null,
    hasMore,
  };
}

module.exports = {
  parseLimit,
  encodeCursor,
  decodeCursor,
  pageResult,
};
