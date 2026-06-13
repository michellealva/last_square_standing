import { call } from 'frappe-ui'

const M = 'last_square_standing.api.'

export const api = {
  createRoom: (username, room_name) =>
    call(M + 'create_room', { username, room_name }),
  joinRoom: (room_code, username) =>
    call(M + 'join_room', { room_code, username }),
  getState: (room_code, player_token) =>
    call(M + 'get_state', { room_code, player_token }),
  startGame: (room_code, player_token) =>
    call(M + 'start_game', { room_code, player_token }),
  submitSelection: (room_code, player_token, selected_square) =>
    call(M + 'submit_selection', { room_code, player_token, selected_square }),
  resolveRound: (room_code) => call(M + 'resolve_round', { room_code }),
  restartGame: (room_code, player_token) =>
    call(M + 'restart_game', { room_code, player_token }),
  playAgain: (room_code, player_token) =>
    call(M + 'play_again', { room_code, player_token }),
  leaveRoom: (room_code, player_token) =>
    call(M + 'leave_room', { room_code, player_token }),
  getLeaderboard: (limit = 10) => call(M + 'get_leaderboard', { limit }),
}
