const tipService = require('../services/tip.service');
const { success } = require('../utils/response');

async function analyze(req, res, next) {
  try {
    const tip = await tipService.createAnalysisRequest(req.user.id, req.body.imageUrls);
    return success(res, { tipId: tip.id, status: tip.status }, 201);
  } catch (err) {
    next(err);
  }
}

async function getTip(req, res, next) {
  try {
    const tip = await tipService.getTip(req.params.tipId, req.user.id);
    return success(res, {
      tipId: tip.id,
      status: tip.status,
      progress: tip.progress,
      results: tip.results,
      errorMsg: tip.error_msg,
    });
  } catch (err) {
    next(err);
  }
}

async function sendTip(req, res, next) {
  try {
    const data = await tipService.sendTip(req.params.tipId, req.body.petId, req.user.id);
    return success(res, data, 201);
  } catch (err) {
    next(err);
  }
}

module.exports = {
  analyze,
  getTip,
  sendTip,
};
