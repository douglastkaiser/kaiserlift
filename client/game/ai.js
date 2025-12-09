import { PieceType } from "./state.js";

export class StonesAI {
  constructor(color) {
    this.color = color;
  }

  chooseMove(_game) {
    throw new Error("chooseMove must be implemented by subclasses");
  }
}

export class RandomAI extends StonesAI {
  constructor(color, bias = 0.7) {
    super(color);
    this.placeBias = bias;
  }

  chooseMove(game) {
    const legal = game.getLegalMoves(this.color);
    if (!legal.length) return null;
    const placeMoves = legal.filter((m) => m.kind === "place");
    const moveMoves = legal.filter((m) => m.kind === "move");
    const earlyGame = game.moveNumber < game.board.length * 2;
    if (earlyGame && placeMoves.length && Math.random() < this.placeBias) {
      return placeMoves[Math.floor(Math.random() * placeMoves.length)];
    }
    return legal[Math.floor(Math.random() * legal.length)];
  }
}

export class HeuristicAI extends StonesAI {
  constructor(color) {
    super(color);
  }

  chooseMove(game) {
    const legal = game.getLegalMoves(this.color);
    if (!legal.length) return null;

    let bestMove = legal[0];
    let bestScore = -Infinity;
    for (const move of legal) {
      const score = this.scoreMove(game, move);
      if (score > bestScore) {
        bestScore = score;
        bestMove = move;
      }
    }
    return bestMove;
  }

  scoreMove(game, move) {
    const next = game.applyMove(move);
    const opponent = game.otherPlayer(this.color);

    if (next.checkWin(this.color)) return 1000;
    if (next.checkWin(opponent)) return -900;

    const myDistance = next.roadDistance(this.color);
    const oppDistance = next.roadDistance(opponent);
    const roadPressure = (isFinite(oppDistance) ? oppDistance : 10) - (isFinite(myDistance) ? myDistance : 10);
    const center = next.centerControl(this.color) - next.centerControl(opponent) * 0.25;
    const capstoneFlex = next.capstoneMobility(this.color) * 0.5;

    let capstonePenalty = 0;
    if (move.kind === "place" && move.piece === PieceType.CAPSTONE && game.moveNumber < 6) {
      capstonePenalty -= 3;
    }

    let blockBonus = 0;
    if (game.isNearWin(opponent)) {
      const threatGapBefore = game.roadDistance(opponent);
      const threatGapAfter = next.roadDistance(opponent);
      blockBonus = Math.max(0, threatGapAfter - threatGapBefore) * 2;
    }

    let extensionBonus = 0;
    if (game.isNearWin(this.color)) {
      extensionBonus += 3;
    }

    return (
      roadPressure * 2 +
      center * 0.3 +
      capstoneFlex +
      blockBonus +
      extensionBonus +
      capstonePenalty
    );
  }
}

export function createAI(difficulty, color) {
  if (difficulty === "medium") return new HeuristicAI(color);
  return new RandomAI(color);
}
