#include "http_server.h"

#include "morph_dict/common/utilit.h"

#ifdef WIN32
#include <process.h>
#include <signal.h>
#pragma comment(lib, "Ws2_32.lib")
#else
#include <sys/signal.h>
#endif


#ifdef WIN32
void InitSocketsWindows() {

	uint16_t wVersionRequested;
	WSADATA wsaData;
	int err;

	/* Use the MAKEWORD(lowbyte, highbyte) macro declared in Windef.h */
	wVersionRequested = MAKEWORD(2, 2);

	err = WSAStartup(wVersionRequested, &wsaData);
	if (err != 0) {
		/* Tell the user that we could not find a usable */
		/* Winsock DLL.                                  */
		printf("WSAStartup failed with error: %d\n", err);
		exit(1);
	}
}
#endif

bool InitSockets() {

#ifdef WIN32
	InitSocketsWindows();
#endif

	if (!event_init()) {
		std::cerr << "Failed to init libevent." << std::endl;
		return false;
	}

	return true;
}

int GetPID() {
#ifdef WIN32
	return _getpid();
#else
	return getpid();
#endif
}

void  termination_handler(int signum) {
	LOGI << "termination_handler daemon";
	exit(1);
};


TRMLHttpServer::TRMLHttpServer() : Server(nullptr, nullptr) {
};

void TRMLHttpServer::Initialize(std::string host, uint16_t port) {
	LOGI << "initialize daemon at " << host << ":" << port;
	InitSockets();
	Server = TInnerServer(evhttp_start(host.c_str(), port), &evhttp_free);
	if (!Server) {
		throw CExpc("Failed to create http server.");
	}

	evhttp_set_default_content_type(Server.get(), "application/json; charset=utf8");
	// Accept both GET and POST requests
	evhttp_set_allowed_methods(Server.get(), EVHTTP_REQ_GET | EVHTTP_REQ_POST | EVHTTP_REQ_OPTIONS);
	if (signal(SIGTERM, termination_handler) == SIG_IGN)
		signal(SIGTERM, SIG_IGN);
};


static void OnHttpRequestStatic(evhttp_request *req, void* httpServer) {
	static_cast<TRMLHttpServer*>(httpServer)->OnHttpRequest(req);
}

void TRMLHttpServer::Start() {
	LOGI<< "run message loop for daemon, start listen socket";
	evhttp_set_gencb(Server.get(), OnHttpRequestStatic, this);
	if (event_dispatch() == -1)	{
		throw CExpc ("Failed to run message loop.");
	}
}

void SendReply(evhttp_request *req, int status, struct evbuffer* response) {
	evhttp_add_header(evhttp_request_get_output_headers(req),
		"Access-Control-Allow-Origin", "*");
	evhttp_send_reply(req, status, "OK", response);
}

void TRMLHttpServer::OnHttpRequest(evhttp_request *req) {
	auto *outBuf = evhttp_request_get_output_buffer(req);
	if (!outBuf)
		return;

	auto cmdType = evhttp_request_get_command(req);
	LOGI << "request method: " << cmdType << " (GET=1,POST=2,OPTIONS=16)";

	// Handle CORS preflight
	if (cmdType == EVHTTP_REQ_OPTIONS) {
		auto *outHdrs = evhttp_request_get_output_headers(req);
		evhttp_add_header(outHdrs, "Access-Control-Allow-Origin", "*");
		evhttp_add_header(outHdrs, "Access-Control-Allow-Methods", "GET, POST, OPTIONS");
		evhttp_add_header(outHdrs, "Access-Control-Allow-Headers", "Content-Type");
		evhttp_send_reply(req, HTTP_OK, "OK", nullptr);
		return;
	}

	const char* uri = evhttp_request_get_uri(req);
	LOGI << uri;
	struct evkeyvalq headers {};
	evhttp_parse_query(uri, &headers);

	try {
		std::string inputQuery;
		std::string postBody;

		// Read POST body if present
		if (cmdType == EVHTTP_REQ_POST) {
			auto *inBuf = evhttp_request_get_input_buffer(req);
			if (inBuf) {
				size_t len = evbuffer_get_length(inBuf);
				LOGI << "POST body length: " << len;
				if (len > 0) {
					auto *data = evbuffer_pullup(inBuf, len);
					postBody.assign(reinterpret_cast<const char*>(data), len);
				}
			}
		}

		// Determine if POST body is URL-encoded form data
		if (!postBody.empty()) {
			// Fetch Content-Type from actual input headers (req->input_headers)
			const char* contentType = evhttp_find_header(evhttp_request_get_input_headers(req), "Content-Type");
			bool isFormEncoded = contentType && strstr(contentType, "application/x-www-form-urlencoded") != nullptr;

			if (isFormEncoded) {
				// Parse form data and merge parameters into headers
				evkeyvalq formParams{};
				if (evhttp_parse_query_str(postBody.c_str(), &formParams) == 0) {
					// Extract 'query' from form data
					auto* formQuery = evhttp_find_header(&formParams, "query");
					if (formQuery) {
						inputQuery = formQuery;
					}
					// Merge all form parameters into main headers (form overrides URL)
					for (auto* kv = formParams.tqh_first; kv != nullptr; kv = kv->next.tqe_next) {
						evhttp_add_header(&headers, kv->key, kv->value);
					}
				}
				evhttp_clear_headers(&formParams);
			}
			
			if (inputQuery.empty()) {
				// Raw text body or missing 'query' parameter
				inputQuery = postBody;
			}
		}

		auto action = evhttp_find_header(&headers, "action");
		if (action == nullptr) {
			throw CExpc("cannot find action");
		}

		auto languaStr = evhttp_find_header(&headers, "langua");
		if (languaStr == nullptr) {
			throw CExpc("cannot find language (langua argument)");
		}
		MorphLanguageEnum langua;
		if (!GetLanguageByString(languaStr, langua)) {
			throw CExpc(Format("unsupported language: %s", languaStr));
		}

		// Fallback to URL query parameter if no input yet
		if (inputQuery.empty()) {
			auto query = evhttp_find_header(&headers, "query");
			if (query == nullptr) {
				throw CExpc("cannot find query");
			}
			inputQuery = query;
		}


		Trim(inputQuery);
		if (inputQuery.empty()) {
			throw CExpc("Empty input query");
		};
		TDaemonParsedRequest parsedRequest{ req, uri, headers, action, langua, inputQuery};
		auto result = OnParsedRequest(parsedRequest);
		evbuffer_add_printf(outBuf, "%s", result.c_str());
		SendReply(req, HTTP_OK, nullptr);
	}
	catch (std::exception& e) {
		LOGE << "Error: " << e.what() << " Request: "  << uri;
		SendReply(req, HTTP_BADREQUEST, nullptr);
		return;
	}

};

void DealWithLockFile(const std::string fileName) {
	std::string LockFileName = MakePath(GetRmlVariable(), fileName);

	if (FileExists(LockFileName.c_str())) {
		LOGI << "possible port conflicts..., removing " << LockFileName;
		remove(LockFileName.c_str());
	}
	FILE* fp = fopen(LockFileName.c_str(), "w");
	if (!fp) {
		throw CExpc(Format("Cannot create file %s", LockFileName.c_str()));
	};
	fprintf(fp, "%i", GetPID());
	fclose(fp);
}

std::string GetLogPath(std::string filename) {
    std::string logPath = GetRegistryString("Software\\Dialing\\Logs\\Main");

    if (!fs::exists(logPath.c_str())) {
        throw CExpc(Format("log directory \"%s\" does not exist, please create it", logPath.c_str()));
    };
    auto path = fs::path(logPath) / filename;
    try {
        FILE *fp = fopen(path.c_str(), "a");
        fclose(fp);
    }
    catch (...) {
        throw CExpc("cannot append to log file %s", path.c_str());
    }
    return path.string();
}
