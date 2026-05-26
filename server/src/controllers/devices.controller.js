const { success } = require('../utils/response');
const deviceService = require('../services/device.service');

async function registerDevice(req, res, next) {
  try {
    const { token, platform } = req.body;
    const data = await deviceService.registerDeviceToken(req.user.id, token, platform);
    return success(res, data, 201);
  } catch (err) {
    next(err);
  }
}

async function removeDevice(req, res, next) {
  try {
    await deviceService.removeDeviceToken(req.user.id, req.params.tokenId);
    return success(res, { success: true });
  } catch (err) {
    next(err);
  }
}

module.exports = {
  registerDevice,
  removeDevice,
};
