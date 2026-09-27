const userModel = require('../models/user.model');

async function deleteUser(id) {
  await userModel.deleteById(id);
}

module.exports = { deleteUser };
