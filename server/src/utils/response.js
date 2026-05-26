function success(res, data = null, status = 200) {
  return res.status(status).json(data);
}

function error(res, code, message, status = 500, fields = undefined) {
  const payload = { code, message };
  if (fields) payload.fields = fields;
  return res.status(status).json(payload);
}

module.exports = { success, error };
