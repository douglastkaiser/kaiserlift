import { BOARD_SIZE, GameState, PieceType } from "./state.js";
import { createAI } from "./ai.js";

const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");
const thinkingEl = document.getElementById("thinking");
const modeLabel = document.getElementById("mode-label");
const actionSelect = document.getElementById("actionSelect");
const difficultySelect = document.getElementById("difficulty");

let state = GameState.fresh();
let currentMode = "local";
let aiPlayer = null;
let selectedCell = null;

function renderBoard() {
  boardEl.innerHTML = "";
  boardEl.style.setProperty("--size", BOARD_SIZE);
  for (let r = 0; r < BOARD_SIZE; r += 1) {
    for (let c = 0; c < BOARD_SIZE; c += 1) {
      const cell = document.createElement("button");
      cell.classList.add("cell");
      cell.dataset.row = r;
      cell.dataset.col = c;
      const stack = state.board[r][c];
      if (stack.length) {
        const top = stack[stack.length - 1];
        cell.textContent = `${top.player}${top.type === PieceType.CAPSTONE ? "□" : ""}`;
        cell.classList.add(top.player === "W" ? "white" : "black");
      } else {
        cell.textContent = "";
      }
      if (selectedCell && selectedCell.row === r && selectedCell.col === c) {
        cell.classList.add("selected");
      }
      boardEl.appendChild(cell);
    }
  }
}

function setStatus(message) {
  statusEl.textContent = message;
}

function announceTurn() {
  setStatus(`Turn ${state.moveNumber + 1}: ${state.currentPlayer === "W" ? "White" : "Black"}`);
}

function resetSelection() {
  selectedCell = null;
  renderBoard();
}

function tryPlace(row, col, piece) {
  try {
    state = state.applyMove({ kind: "place", row, col, piece });
    return true;
  } catch (err) {
    console.warn(err.message);
    return false;
  }
}

function tryMove(from, to) {
  try {
    state = state.applyMove({ kind: "move", from, to });
    return true;
  } catch (err) {
    console.warn(err.message);
    return false;
  }
}

function handleCellClick(event) {
  if (aiTurn()) return;
  const row = Number(event.target.dataset.row);
  const col = Number(event.target.dataset.col);
  const action = actionSelect.value;

  if (action.startsWith("place")) {
    if (!state.isEmpty(row, col)) return;
    const piece = action === "place-capstone" ? PieceType.CAPSTONE : PieceType.FLAT;
    const moved = tryPlace(row, col, piece);
    if (moved) afterMove();
    return;
  }

  const top = state.topPiece(row, col);
  if (!selectedCell) {
    if (top?.player !== state.currentPlayer) return;
    selectedCell = { row, col };
    renderBoard();
    return;
  }

  if (selectedCell.row === row && selectedCell.col === col) {
    resetSelection();
    return;
  }

  const moved = tryMove(selectedCell, { row, col });
  resetSelection();
  if (moved) afterMove();
}

function aiTurn() {
  return aiPlayer && state.currentPlayer === aiPlayer.color;
}

function afterMove() {
  renderBoard();
  if (state.checkWin("W")) {
    setStatus("White wins by road!");
    return;
  }
  if (state.checkWin("B")) {
    setStatus("Black wins by road!");
    return;
  }
  announceTurn();
  if (aiTurn()) {
    scheduleAIMove();
  }
}

function scheduleAIMove() {
  thinkingEl.classList.remove("hidden");
  setTimeout(() => {
    const move = aiPlayer.chooseMove(state);
    thinkingEl.classList.add("hidden");
    if (!move) {
      setStatus("AI has no legal moves.");
      return;
    }
    state = state.applyMove(move);
    setStatus(`AI plays ${state.otherPlayer(aiPlayer.color)} to move next`);
    afterMove();
  }, 500);
}

function startLocal() {
  currentMode = "local";
  aiPlayer = null;
  difficultySelect.classList.add("hidden");
  modeLabel.textContent = "Local Game (hot seat)";
  state = GameState.fresh();
  selectedCell = null;
  renderBoard();
  announceTurn();
}

function startVsComputer() {
  currentMode = "ai";
  difficultySelect.classList.remove("hidden");
  const difficulty = document.querySelector("input[name=difficulty]:checked")?.value ?? "easy";
  aiPlayer = createAI(difficulty, "B");
  modeLabel.textContent = `vs Computer — ${difficulty[0].toUpperCase()}${difficulty.slice(1)}`;
  state = GameState.fresh();
  state.currentPlayer = "W"; // Human starts as White
  selectedCell = null;
  renderBoard();
  announceTurn();
}

function bindMenu() {
  document.getElementById("localBtn").addEventListener("click", () => startLocal());
  document.getElementById("aiBtn").addEventListener("click", () => startVsComputer());
  document.querySelectorAll("input[name=difficulty]").forEach((input) => {
    input.addEventListener("change", () => {
      if (currentMode === "ai") startVsComputer();
    });
  });
}

function init() {
  bindMenu();
  boardEl.addEventListener("click", handleCellClick);
  renderBoard();
  announceTurn();
}

init();
