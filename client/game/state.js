export const BOARD_SIZE = 5;
export const PieceType = {
  FLAT: "flat",
  CAPSTONE: "capstone",
};

const DIRECTIONS = [
  { dr: -1, dc: 0, name: "up" },
  { dr: 1, dc: 0, name: "down" },
  { dr: 0, dc: -1, name: "left" },
  { dr: 0, dc: 1, name: "right" },
];

function cloneBoard(board) {
  return board.map((row) => row.map((stack) => [...stack]));
}

function inBounds(row, col) {
  return row >= 0 && row < BOARD_SIZE && col >= 0 && col < BOARD_SIZE;
}

export class GameState {
  constructor({ board, currentPlayer = "W", moveNumber = 0, reserves } = {}) {
    this.board = board ??
      Array.from({ length: BOARD_SIZE }, () =>
        Array.from({ length: BOARD_SIZE }, () => [])
      );
    this.currentPlayer = currentPlayer;
    this.moveNumber = moveNumber;
    this.reserves =
      reserves ?? {
        W: { flats: 21, capstones: 1 },
        B: { flats: 21, capstones: 1 },
      };
  }

  static fresh() {
    return new GameState();
  }

  clone() {
    return new GameState({
      board: cloneBoard(this.board),
      currentPlayer: this.currentPlayer,
      moveNumber: this.moveNumber,
      reserves: {
        W: { ...this.reserves.W },
        B: { ...this.reserves.B },
      },
    });
  }

  otherPlayer(player) {
    return player === "W" ? "B" : "W";
  }

  isEmpty(row, col) {
    return this.board[row][col].length === 0;
  }

  topPiece(row, col) {
    const stack = this.board[row][col];
    return stack[stack.length - 1];
  }

  capstonePositions(player) {
    const positions = [];
    for (let r = 0; r < BOARD_SIZE; r += 1) {
      for (let c = 0; c < BOARD_SIZE; c += 1) {
        const top = this.topPiece(r, c);
        if (top?.player === player && top.type === PieceType.CAPSTONE) {
          positions.push({ row: r, col: c });
        }
      }
    }
    return positions;
  }

  placeMove(row, col, type = PieceType.FLAT, player = this.currentPlayer) {
    if (!inBounds(row, col) || !this.isEmpty(row, col)) {
      throw new Error("Invalid placement");
    }
    const reserves = this.reserves[player];
    if (type === PieceType.CAPSTONE) {
      if (reserves.capstones <= 0) throw new Error("No capstones left");
      reserves.capstones -= 1;
    } else if (reserves.flats <= 0) {
      throw new Error("No flats left");
    } else {
      reserves.flats -= 1;
    }
    this.board[row][col].push({ player, type });
  }

  moveStack(fromRow, fromCol, toRow, toCol, player = this.currentPlayer) {
    if (!inBounds(fromRow, fromCol) || !inBounds(toRow, toCol)) {
      throw new Error("Move out of bounds");
    }
    const stack = this.board[fromRow][fromCol];
    if (!stack.length || this.topPiece(fromRow, fromCol).player !== player) {
      throw new Error("Cannot move that stack");
    }
    const distance = Math.abs(fromRow - toRow) + Math.abs(fromCol - toCol);
    if (distance !== 1) {
      throw new Error("Only simple adjacent moves are supported");
    }
    if (!this.isEmpty(toRow, toCol)) {
      throw new Error("Destination must be empty for now");
    }
    this.board[toRow][toCol] = [...stack];
    this.board[fromRow][fromCol] = [];
  }

  applyMove(move) {
    const next = this.clone();
    if (move.kind === "place") {
      next.placeMove(move.row, move.col, move.piece, next.currentPlayer);
    } else if (move.kind === "move") {
      next.moveStack(
        move.from.row,
        move.from.col,
        move.to.row,
        move.to.col,
        next.currentPlayer,
      );
    }
    next.currentPlayer = this.otherPlayer(next.currentPlayer);
    next.moveNumber += 1;
    return next;
  }

  getLegalMoves(player = this.currentPlayer) {
    const moves = [];
    // Placements
    for (let r = 0; r < BOARD_SIZE; r += 1) {
      for (let c = 0; c < BOARD_SIZE; c += 1) {
        if (this.isEmpty(r, c)) {
          if (this.reserves[player].flats > 0) {
            moves.push({ kind: "place", row: r, col: c, piece: PieceType.FLAT });
          }
          if (this.reserves[player].capstones > 0) {
            moves.push({ kind: "place", row: r, col: c, piece: PieceType.CAPSTONE });
          }
        }
      }
    }
    // Simple slide moves (adjacent, into empty)
    for (let r = 0; r < BOARD_SIZE; r += 1) {
      for (let c = 0; c < BOARD_SIZE; c += 1) {
        const top = this.topPiece(r, c);
        if (!top || top.player !== player) continue;
        for (const dir of DIRECTIONS) {
          const nr = r + dir.dr;
          const nc = c + dir.dc;
          if (inBounds(nr, nc) && this.isEmpty(nr, nc)) {
            moves.push({
              kind: "move",
              from: { row: r, col: c },
              to: { row: nr, col: nc },
              direction: dir.name,
            });
          }
        }
      }
    }
    return moves;
  }

  checkWin(player) {
    const targetEdge = player === "W" ? BOARD_SIZE - 1 : BOARD_SIZE - 1;
    const visited = Array.from({ length: BOARD_SIZE }, () =>
      Array.from({ length: BOARD_SIZE }, () => false)
    );
    const queue = [];
    if (player === "W") {
      for (let c = 0; c < BOARD_SIZE; c += 1) {
        const top = this.topPiece(0, c);
        if (top?.player === player) {
          queue.push({ row: 0, col: c });
          visited[0][c] = true;
        }
      }
    } else {
      for (let r = 0; r < BOARD_SIZE; r += 1) {
        const top = this.topPiece(r, 0);
        if (top?.player === player) {
          queue.push({ row: r, col: 0 });
          visited[r][0] = true;
        }
      }
    }

    while (queue.length) {
      const { row, col } = queue.shift();
      if ((player === "W" && row === targetEdge) || (player === "B" && col === targetEdge)) {
        return true;
      }
      for (const dir of DIRECTIONS) {
        const nr = row + dir.dr;
        const nc = col + dir.dc;
        if (!inBounds(nr, nc) || visited[nr][nc]) continue;
        const top = this.topPiece(nr, nc);
        if (top?.player === player) {
          visited[nr][nc] = true;
          queue.push({ row: nr, col: nc });
        }
      }
    }
    return false;
  }

  roadDistance(player) {
    const opponent = this.otherPlayer(player);
    const dist = Array.from({ length: BOARD_SIZE }, () =>
      Array.from({ length: BOARD_SIZE }, () => Infinity)
    );
    const pq = [];
    const push = (row, col, cost) => {
      dist[row][col] = cost;
      pq.push({ row, col, cost });
    };

    if (player === "W") {
      for (let c = 0; c < BOARD_SIZE; c += 1) {
        const top = this.topPiece(0, c);
        const cost = top?.player === player ? 0 : top?.player === opponent ? Infinity : 1;
        push(0, c, cost);
      }
    } else {
      for (let r = 0; r < BOARD_SIZE; r += 1) {
        const top = this.topPiece(r, 0);
        const cost = top?.player === player ? 0 : top?.player === opponent ? Infinity : 1;
        push(r, 0, cost);
      }
    }

    while (pq.length) {
      pq.sort((a, b) => a.cost - b.cost);
      const { row, col, cost } = pq.shift();
      if (cost !== dist[row][col]) continue;
      for (const dir of DIRECTIONS) {
        const nr = row + dir.dr;
        const nc = col + dir.dc;
        if (!inBounds(nr, nc)) continue;
        if (dist[nr][nc] <= cost) continue;
        const top = this.topPiece(nr, nc);
        const cellCost = top?.player === player ? 0 : top?.player === opponent ? Infinity : 1;
        if (cellCost === Infinity) continue;
        const nextCost = cost + cellCost;
        if (nextCost < dist[nr][nc]) {
          dist[nr][nc] = nextCost;
          pq.push({ row: nr, col: nc, cost: nextCost });
        }
      }
    }

    let best = Infinity;
    if (player === "W") {
      for (let c = 0; c < BOARD_SIZE; c += 1) {
        best = Math.min(best, dist[BOARD_SIZE - 1][c]);
      }
    } else {
      for (let r = 0; r < BOARD_SIZE; r += 1) {
        best = Math.min(best, dist[r][BOARD_SIZE - 1]);
      }
    }
    return best;
  }

  centerControl(player) {
    const center = (BOARD_SIZE - 1) / 2;
    let score = 0;
    for (let r = 0; r < BOARD_SIZE; r += 1) {
      for (let c = 0; c < BOARD_SIZE; c += 1) {
        const top = this.topPiece(r, c);
        if (top?.player === player) {
          const distance = Math.abs(center - r) + Math.abs(center - c);
          score += Math.max(0, BOARD_SIZE - distance);
        }
      }
    }
    return score;
  }

  capstoneMobility(player) {
    let mobility = 0;
    for (const { row, col } of this.capstonePositions(player)) {
      for (const dir of DIRECTIONS) {
        const nr = row + dir.dr;
        const nc = col + dir.dc;
        if (inBounds(nr, nc) && this.isEmpty(nr, nc)) mobility += 1;
      }
    }
    return mobility;
  }

  isNearWin(player) {
    const distance = this.roadDistance(player);
    return distance <= 2;
  }

  describeMove(move) {
    if (move.kind === "place") {
      const piece = move.piece === PieceType.CAPSTONE ? "capstone" : "flat";
      return `${piece} at ${move.row + 1}-${move.col + 1}`;
    }
    return `move ${move.from.row + 1}-${move.from.col + 1} to ${move.to.row + 1}-${move.to.col + 1}`;
  }
}
