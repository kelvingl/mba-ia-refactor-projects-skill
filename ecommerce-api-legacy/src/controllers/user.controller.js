const userModel = require('../models/user.model');
const { NotFoundError } = require('../utils/errors');

async function deleteUser(id) {
  const changes = await userModel.remove(id);
  if (changes === 0) throw new NotFoundError('Usuário não encontrado');
  return { message: 'Usuário deletado com sucesso' };
}

module.exports = { deleteUser };
