#include <vector>
#include <iostream>
#include <map>
#include <utility>
#include <stdlib.h>
#include <time.h>
#define DEPTH 4
// is treated as the bottom is white and top is black
#define mpair std::make_pair
typedef std::pair<int, int> pii;
typedef int(*MoveFunction)(pii, int);
typedef bool(*BestFunction)(int&, int);
pii ans_from;
pii ans;
#define _DEBUG(expr) (0)
#define _DEBUG2(expr) (0)
#define _DEBUG3(expr) (0)
#define _DEBUG4(expr) (expr)
#define RANDOM_CHANCE 5
bool set_max(int &a, int b) {
	if (b > a) {
		a = b;
		return 1;
	}
	if (b == a && rand() % RANDOM_CHANCE == 0) {
		return 1;
	}
	return 0;
}

bool set_min(int &a, int b) {
	if (b < a) {
		a = b;
		return 1;
	}
	if (b == a && rand() % RANDOM_CHANCE == 0) {
		return 1;
	}
	return 0;
}

struct ChessBoard {
	int _data[8][8]; // x, y
	int *translate = (new int[40]) + 20;
	int *untranslate = (new int [4000]) + 2000;
	MoveFunction *move_func = (new MoveFunction[4000]) + 2000;
	BestFunction *best_func = (new BestFunction[10]) + 5;
	int depth = DEPTH;
	int result = 0;
	inline int &operator()(int i1, int i2) {
		return _data[i1][i2];
	}
	void init_functions();
	void init_translates() {
		translate[0] = 0;
		translate[1] = 1;
		translate[2] = 3;
		translate[3] = 3;
		translate[4] = 5;
		translate[5] = 9;
		translate[6] = 1000;
		for (int i = -6; i <= -1; i++) {
			translate[i] = -translate[-i];
		}
		for (int i = -6; i <= 6; i++) {
			untranslate[translate[i]] = i;
		}
	}
	ChessBoard() {
		init_translates();
		init_functions();
		for (int y = 0; y < 8; y++) {
			for (int x = 0; x < 8; x++) {
				std::cin >> _data[x][y];
			}
		}
	}
	int full_result() {
		int ret = 0;
		for (int y = 0; y < 8; y++) {
			for (int x = 0; x < 8; x++) {
				ret += translate[_data[x][y]];
			}
		}
		return ret;
	}
};
std::ostream & operator<<(std::ostream &out, const ChessBoard &b) {
	for (int y = 0; y < 8; y++) {
		for (int x = 0; x < 8; x++) {
			out << b._data[x][y] << " ";
		}
		out << "\n";
	}
	return out;
}
std::ostream & operator<<(std::ostream &out, const std::pair<int, int> p) {
	return out << p.first << " " << p.second;
}
#define PAWN 1
#define QUEEN 5
#define sign(x) ((x > 0) - (x < 0))
ChessBoard board;
struct ChessMove {
	pii from;
	pii to;
	int at_from;
	int at_to;
	int diff;
	inline ChessMove(const pii &_from, const pii &_to) :
		from(_from), to(_to),
		at_from(board(from.first, from.second)),
		at_to(board(to.first, to.second)) {

		board(from.first, from.second) = 0;
		board(to.first, to.second) = at_from;

		diff = -board.translate[at_to]; // removes at to
		if (at_from == PAWN) {
			if (to.second == 0 || to.second == 7) {
				diff += (-board.translate[PAWN] + board.translate[QUEEN]); // removes pawn, adds queen
				board(to.first, to.second) = sign(at_from) * QUEEN;
			}
		}
		board.result += diff;
	}
	inline ~ChessMove() {
		board.result -= diff;
		board(from.first, from.second) = at_from;
		board(to.first, to.second) = at_to;
	}
};
int move_all(int playing_as) {
	if (!board.depth || abs(board.result) > 500) {
		return board.result;
	}
	board.depth--;
	pii local_ans_from;
	pii local_ans;
	int local_best = -playing_as * 10000;
	for (int y = 0; y < 8; y++) {
		for (int x = 0; x < 8; x++) {
			if (sign(board(x, y)) == playing_as) {
				if (board.best_func[playing_as](local_best, board.move_func[board(x, y)](mpair(x, y), playing_as))) {
					local_ans_from = mpair(x, y);
					local_ans = ans;
				}
			}
		}
	}
	ans_from = local_ans_from;
	ans = local_ans;
	board.depth++;
	return local_best;
}

#define valid_num(nm) (((unsigned int)(nm)) < 8)

#define is_valid(p) (valid_num(p.first) && valid_num(p.second))
#define is_enemy(p) (sign(board(p.first, p.second)) == -playing_as)
#define is_friend(p) (sign(board(p.first, p.second)) == playing_as)
#define is_something(p) (sign(board(p.first, p.second)) != 0)
#define is_empty(p) (sign(board(p.first, p.second)) == 0)

#define next_move() \
	do { \
		ChessMove tmpmove(old_pos, pos); \
		if (board.best_func[playing_as](local_best, move_all(-playing_as))) local_ans = pos; \
	} while (0)

#define test_not_friend() \
	if (!is_friend(pos)) next_move()

#define test_enemy() \
	if (is_enemy(pos)) next_move()

#define test_empty() \
	if (is_empty(pos)) next_move()

#define move_start() \
	pii old_pos = pos; \
	pii local_ans; \
	int local_best = -playing_as * 10000

#define move_end() \
	ans = local_ans; \
	return local_best

//#define MOVE_DOUBLE_PAWN
int move_pawn(pii pos, int playing_as) { // doesnt check if turns queen nor 2 step move (checks now)
	move_start();

	pos.second -= playing_as;
	if (is_valid(pos)) { // if can move one
#ifdef MOVE_DOUBLE_PAWN
		if (is_empty(pos)) { // if empty, test if can move second
			if ((playing_as == -1 && pos.second == 2) || (playing_as == 1 && pos.second == 5)) {
				// if these match, then the position is valid, dont need to test
				pos.second -= playing_as;
				test_empty();
				pos.second += playing_as;
			}
		}
#endif
		test_empty();
	}
	pos.first -= 1;
	if (is_valid(pos)) {
		test_enemy();
	}
	pos.first += 2;
	if (is_valid(pos)) {
		test_enemy();
	}
	move_end();
}

int move_bishop(pii pos, int playing_as) {
	move_start();
	while (true) {
		pos.first += 1, pos.second += 1;
		if (!is_valid(pos)) break;
		test_not_friend();
		if (is_something(pos)) break;
	}
	pos = old_pos;
	while (true) {
		pos.first += 1, pos.second -= 1;
		if (!is_valid(pos)) break;
		test_not_friend();
		if (is_something(pos)) break;
	}
	pos = old_pos;
	while (true) {
		pos.first -= 1, pos.second += 1;
		if (!is_valid(pos)) break;
		test_not_friend();
		if (is_something(pos)) break;
	}
	pos = old_pos;
	while (true) {
		pos.first -= 1, pos.second -= 1;
		if (!is_valid(pos)) break;
		test_not_friend();
		if (is_something(pos)) break;
	}
	move_end();
}
int move_rook(pii pos, int playing_as) {
	move_start();
	while (true) {
		pos.first += 1;
		if (!is_valid(pos)) break;
		test_not_friend();
		if (is_something(pos)) break;
	}
	pos = old_pos;
	while (true) {
		pos.first -= 1;
		if (!is_valid(pos)) break;
		test_not_friend();
		if (is_something(pos)) break;
	}
	pos = old_pos;
	while (true) {
		pos.second += 1;
		if (!is_valid(pos)) break;
		test_not_friend();
		if (is_something(pos)) break;
	}
	pos = old_pos;
	while (true) {
		pos.second -= 1;
		if (!is_valid(pos)) break;
		test_not_friend();
		if (is_something(pos)) break;
	}
	move_end();
}

int move_queen(pii pos, int playing_as) {
	move_start();
	if (board.best_func[playing_as](local_best, move_rook(pos, playing_as))) {
		local_ans = ans;
	}
	if (board.best_func[playing_as](local_best, move_bishop(pos, playing_as))) {
		local_ans = ans;
	}
	move_end();
}

int move_king(pii pos, int playing_as) {
	move_start();
	for (int x = -1; x <= 1; x++) {
		for (int y = -1; y <= 1; y++) {
			if (!x && !y) continue;
			pos.first += x; pos.second += y;
			if (is_valid(pos)) {
				test_not_friend();
			}
			pos.first -= x; pos.second -= y;
		}
	}
	move_end();
}

int move_knight(pii pos, int playing_as) {
	move_start();
	for (int x = -2; x <= 2; x++) {
		if (!x) continue;
		for (int y = -2; y <= 2; y++) {
			if (!y || abs(x) == abs(y)) continue;
			pos.first += x; pos.second += y;
			if (is_valid(pos)) {
				test_not_friend();
			}
			pos.first -= x; pos.second -= y;
		}
	}
	move_end();
}
void ChessBoard::init_functions() {
	MoveFunction tmp[7];
	tmp[1] = move_pawn;
	tmp[2] = move_knight;
	tmp[3] = move_bishop;
	tmp[4] = move_rook;
	tmp[5] = move_queen;
	tmp[6] = move_king;
	for (int i = -6; i <= 6; i++) {
		if (i == 0) continue;
		move_func[i] = tmp[abs(i)];
	}
	best_func[1] = set_max;
	best_func[-1] = set_min;
}
void finish() {
	std::cout << char(ans_from.second + 'a') << ans_from.first + 1;
	std::cout << char(ans.second + 'a') << ans.first + 1 << "\n";
	exit(0);
}

void not_finish() {
	std::cerr << char(ans_from.second + 'a') << ans_from.first + 1;
	std::cerr << char(ans.second + 'a') << ans.first + 1 << "\n";
}
int main() {
	srandom(time(NULL));
	std::cerr << "current - " << board.full_result() << "\n";
	for (int i = DEPTH; i >= 1; i--) {
		board.depth = i;
		int prediction = move_all(1);
		std::cerr << "prediction - " << prediction << "\n";
		std::cerr << "depth - " << i << "\n";
		if (prediction > -500) {
			finish();
		}
		else {
			not_finish();
		}
		
	}
	std::cerr << "big failure\n";
	finish();
}
