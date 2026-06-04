// ============================================================
//  BACKEND — backend/server.cpp
//  C++ Game Server: Auth, Scores, Game Logic over TCP sockets
// ============================================================

#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <sstream>
#include <fstream>
#include <cmath>
#include <algorithm>
#include <cstring>
#include <ctime>
#include <thread>
#include <mutex>

#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #pragma comment(lib, "ws2_32.lib")
  typedef SOCKET sock_t;
#else
  #include <sys/socket.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
  #include <unistd.h>
  typedef int sock_t;
  #define INVALID_SOCKET -1
  #define closesocket close
#endif

#include <sqlite3.h>

#define PORT 9999
#define BUFSIZE 4096

static sqlite3* g_db = nullptr;
static std::mutex g_db_mutex;

static std::string sha_simple(const std::string& s) {
    unsigned long h = 5381;
    for (char c : s) h = ((h << 5) + h) + c;
    std::ostringstream ss; ss << std::hex << h;
    return ss.str();
}

bool db_init(const char* path) {
    int rc = sqlite3_open(path, &g_db);
    if (rc != SQLITE_OK) { std::cerr << "DB error\n"; return false; }
    const char* sql = R"(
        CREATE TABLE IF NOT EXISTS players(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created  TEXT DEFAULT(datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS scores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER, level_id INTEGER,
            score INTEGER, stars INTEGER,
            time_taken INTEGER, wrong_clicks INTEGER,
            hints_used INTEGER,
            played_at TEXT DEFAULT(datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY, value TEXT
        );
    )";
    char* err = nullptr;
    sqlite3_exec(g_db, sql, nullptr, nullptr, &err);
    if (err) { std::cerr << "Schema: " << err; sqlite3_free(err); return false; }
    std::cout << "[DB] Ready at " << path << "\n";
    return true;
}

static std::string db_query_single(const char* sql, std::vector<std::string> params = {}) {
    std::lock_guard<std::mutex> lock(g_db_mutex);
    sqlite3_stmt* stmt;
    sqlite3_prepare_v2(g_db, sql, -1, &stmt, nullptr);
    for (int i = 0; i < (int)params.size(); i++)
        sqlite3_bind_text(stmt, i+1, params[i].c_str(), -1, SQLITE_STATIC);
    std::string result = "";
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        const char* v = (const char*)sqlite3_column_text(stmt, 0);
        if (v) result = v;
    }
    sqlite3_finalize(stmt);
    return result;
}

static bool db_exec(const char* sql, std::vector<std::string> params = {}) {
    std::lock_guard<std::mutex> lock(g_db_mutex);
    sqlite3_stmt* stmt;
    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, nullptr);
    if (rc != SQLITE_OK) return false;
    for (int i = 0; i < (int)params.size(); i++)
        sqlite3_bind_text(stmt, i+1, params[i].c_str(), -1, SQLITE_STATIC);
    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return (rc == SQLITE_DONE || rc == SQLITE_ROW);
}

static std::string ok(const std::string& data = "") { return "OK" + (data.empty() ? "" : "|" + data) + "\n"; }
static std::string err(const std::string& msg) { return "ERR|" + msg + "\n"; }

static std::vector<std::string> split(const std::string& s, char delim) {
    std::vector<std::string> out;
    std::istringstream ss(s);
    std::string tok;
    while (std::getline(ss, tok, delim)) out.push_back(tok);
    return out;
}

std::string handle_signup(const std::vector<std::string>& args) {
    if (args.size() < 3) return err("Usage: SIGNUP|username|password");
    std::string user = args[1], pass = sha_simple(args[2]);
    if (!db_exec("INSERT INTO players(username,password) VALUES(?,?)", {user, pass})) {
        return err("Username already taken");
    }
    std::string id = db_query_single("SELECT id FROM players WHERE username=?", {user});
    return ok(id + "|" + user);
}

std::string handle_login(const std::vector<std::string>& args) {
    if (args.size() < 3) return err("Usage: LOGIN|username|password");
    std::string user = args[1], pass = sha_simple(args[2]);
    std::string id = db_query_single("SELECT id FROM players WHERE username=? AND password=?", {user, pass});
    if (id.empty()) return err("Invalid username or password");
    return ok(id + "|" + user);
}

std::string handle_save_score(const std::vector<std::string>& args) {
    if (args.size() < 8) return err("Bad args");
    db_exec("INSERT INTO scores(player_id,level_id,score,stars,time_taken,wrong_clicks,hints_used) VALUES(?,?,?,?,?,?,?)",
        {args[1],args[2],args[3],args[4],args[5],args[6],args[7]});
    return ok("Score saved");
}

std::string handle_best_score(const std::vector<std::string>& args) {
    if (args.size() < 3) return err("Bad args");
    //Explicitly CAST score to INTEGER to avoid '10' < '9' string comparison issues.
    std::string best = db_query_single(
        "SELECT MAX(CAST(score AS INTEGER)) FROM scores WHERE player_id=? AND level_id=?",
        {args[1], args[2]});
    return ok(best.empty() || best == "NULL" ? "-1" : best);
}

std::string handle_leaderboard(const std::vector<std::string>& args) {
    std::lock_guard<std::mutex> lock(g_db_mutex);
    //Order by integer representation of score
    const char* sql = R"(
        SELECT p.username, s.score, s.level_id, s.stars, s.played_at
        FROM scores s JOIN players p ON s.player_id=p.id
        ORDER BY CAST(s.score AS INTEGER) DESC LIMIT 10
    )";
    sqlite3_stmt* stmt;
    sqlite3_prepare_v2(g_db, sql, -1, &stmt, nullptr);
    std::string result = "";
    while (sqlite3_step(stmt) == SQLITE_ROW) {
        if (!result.empty()) result += ";";
        result += std::string((const char*)sqlite3_column_text(stmt,0)) + ","
               + std::string((const char*)sqlite3_column_text(stmt,1)) + ","
               + std::string((const char*)sqlite3_column_text(stmt,2)) + ","
               + std::string((const char*)sqlite3_column_text(stmt,3)) + ","
               + std::string((const char*)sqlite3_column_text(stmt,4));
    }
    sqlite3_finalize(stmt);
    return ok(result.empty() ? "EMPTY" : result);
}

std::string handle_is_unlocked(const std::vector<std::string>& args) {
    if (args.size() < 3) return err("Bad args");
    int level_id = std::stoi(args[2]);
    if (level_id <= 1) return ok("1");
    //CAST to handle numeric checks correctly
    std::string best = db_query_single(
        "SELECT MAX(CAST(score AS INTEGER)) FROM scores WHERE player_id=? AND level_id=?",
        {args[1], std::to_string(level_id - 1)});
    bool unlocked = (!best.empty() && best != "NULL" && std::stoi(best) > 0);
    return ok(unlocked ? "1" : "0");
}

std::string handle_calc_score(const std::vector<std::string>& args) {
    if (args.size() < 8) return err("Bad args");
    int found      = std::stoi(args[1]);
    int time_left  = std::stoi(args[3]);
    int wrong      = std::stoi(args[5]);
    int hints      = std::stoi(args[7]);

    int score = found * 100 + time_left * 5 - wrong * 25 - hints * 50;
    score = std::max(0, score);

    int total_diffs = std::stoi(args[2]);
    int time_limit  = std::stoi(args[4]);
    int max_lives   = std::stoi(args[6]);
    int max_score   = total_diffs * 100 + time_limit * 5 + max_lives * 50;
    int stars = (max_score > 0 && score >= max_score * 0.8) ? 3
              : (max_score > 0 && score >= max_score * 0.5) ? 2 : 1;

    return ok(std::to_string(score) + "|" + std::to_string(stars));
}

std::string handle_ping() { return ok("PONG"); }

std::string dispatch(const std::string& raw) {
    std::string line = raw;
    while (!line.empty() && (line.back()=='\n'||line.back()=='\r')) line.pop_back();
    if (line.empty()) return ok("EMPTY");

    auto parts = split(line, '|');
    if (parts.empty()) return err("Empty command");
    std::string cmd = parts[0];

    if      (cmd == "PING")         return handle_ping();
    else if (cmd == "SIGNUP")       return handle_signup(parts);
    else if (cmd == "LOGIN")        return handle_login(parts);
    else if (cmd == "SAVE_SCORE")   return handle_save_score(parts);
    else if (cmd == "BEST_SCORE")   return handle_best_score(parts);
    else if (cmd == "LEADERBOARD")  return handle_leaderboard(parts);
    else if (cmd == "IS_UNLOCKED")  return handle_is_unlocked(parts);
    else if (cmd == "CALC_SCORE")   return handle_calc_score(parts);
    else return err("Unknown command: " + cmd);
}

void handle_client(sock_t client_sock) {
    char buf[BUFSIZE];
    while (true) {
        memset(buf, 0, BUFSIZE);
        int n = recv(client_sock, buf, BUFSIZE - 1, 0);
        if (n <= 0) break;
        std::string request(buf, n);
        std::string response = dispatch(request);
        send(client_sock, response.c_str(), (int)response.size(), 0);
    }
    closesocket(client_sock);
}

int main() {
#ifdef _WIN32
    WSADATA wsa; WSAStartup(MAKEWORD(2,2), &wsa);
#endif

    if (!db_init("../data/scores.db")) return 1;

    sock_t server = socket(AF_INET, SOCK_STREAM, 0);
    if (server == INVALID_SOCKET) { std::cerr << "Socket failed\n"; return 1; }

    int opt = 1;
    setsockopt(server, SOL_SOCKET, SO_REUSEADDR, (char*)&opt, sizeof(opt));

    sockaddr_in addr{};
    addr.sin_family      = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port        = htons(PORT);

    if (bind(server, (sockaddr*)&addr, sizeof(addr)) < 0) {
        std::cerr << "Bind failed\n"; return 1;
    }
    listen(server, 10);
    std::cout << "[Server] Listening on port " << PORT << "\n";

    while (true) {
        sockaddr_in client_addr{};
        socklen_t client_len = sizeof(client_addr);
        sock_t client = accept(server, (sockaddr*)&client_addr, &client_len);
        if (client == INVALID_SOCKET) continue;
        std::cout << "[Server] Client connected\n";
        std::thread(handle_client, client).detach();
    }

    closesocket(server);
#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}