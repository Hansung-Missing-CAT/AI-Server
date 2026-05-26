const petService = require('../services/pet.service');
const { success } = require('../utils/response');
const { parseLimit } = require('../utils/pagination');
const { enqueueEmbeddingIndex } = require('../queues/producers/embedding.producer');
const { enqueuePushNotification } = require('../queues/producers/push.producer');

async function listPets(req, res, next) {
  try {
    const result = await petService.listPets({
      district: req.query.district,
      q: req.query.q,
      sort: req.query.sort,
      status: req.query.status,
      cursor: req.query.cursor,
      limit: parseLimit(req.query.limit),
    });
    return success(res, result);
  } catch (err) {
    next(err);
  }
}

async function getPet(req, res, next) {
  try {
    const pet = await petService.getPetById(req.params.id);
    await petService.incrementViews(req.params.id);
    const isLiked = req.user?.id ? await petService.isPetLikedByUser(req.params.id, req.user.id) : false;
    return success(res, { ...pet, isLiked });
  } catch (err) {
    next(err);
  }
}

async function createPet(req, res, next) {
  try {
    const pet = await petService.createPet(req.body, req.user.id);
    enqueueEmbeddingIndex({ petId: pet.id }).catch(() => undefined);
    enqueuePushNotification({ type: 'nearby_report', petId: pet.id }).catch(() => undefined);
    return success(res, pet, 201);
  } catch (err) {
    next(err);
  }
}

async function patchPet(req, res, next) {
  try {
    const pet = await petService.updatePet(req.params.id, req.body, req.user.id);
    return success(res, pet);
  } catch (err) {
    next(err);
  }
}

async function removePet(req, res, next) {
  try {
    await petService.deletePet(req.params.id, req.user.id);
    return success(res, { success: true });
  } catch (err) {
    next(err);
  }
}

async function likePet(req, res, next) {
  try {
    await petService.likePet(req.params.id, req.user.id);
    return success(res, { success: true }, 201);
  } catch (err) {
    next(err);
  }
}

async function unlikePet(req, res, next) {
  try {
    await petService.unlikePet(req.params.id, req.user.id);
    return success(res, { success: true });
  } catch (err) {
    next(err);
  }
}

async function listComments(req, res, next) {
  try {
    const result = await petService.listComments(req.params.id, {
      cursor: req.query.cursor,
      limit: parseLimit(req.query.limit),
    });
    return success(res, result);
  } catch (err) {
    next(err);
  }
}

async function createComment(req, res, next) {
  try {
    const comment = await petService.createComment(req.params.id, req.user.id, req.body.content);
    return success(res, comment, 201);
  } catch (err) {
    next(err);
  }
}

async function removeComment(req, res, next) {
  try {
    await petService.deleteComment(req.params.commentId, req.user.id);
    return success(res, { success: true });
  } catch (err) {
    next(err);
  }
}

module.exports = {
  listPets,
  getPet,
  createPet,
  patchPet,
  removePet,
  likePet,
  unlikePet,
  listComments,
  createComment,
  removeComment,
};
