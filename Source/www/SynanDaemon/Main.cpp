#include "SynanDmn.h"

#include "morph_dict/common/utilit.h"
#include "morph_dict/common/argparse.h"

void initArgParser(int argc, const char **argv, ArgumentParser& parser) {
    parser.AddArgument("--host", "0.0.0.0 or other ip");
    parser.AddArgument("--port", "17018");
    parser.AddArgument("--log-level", "log level", true);
	parser.AddOption("--skipbigrams");
	parser.Parse(argc, argv);
}

int	main(int argc, const char **argv) {
	ArgumentParser args;
	initArgParser(argc, argv, args);
    auto log_path = GetLogPath("synan_dmn.log");
    init_plog(args.GetLogLevel(), log_path, false);
	bool skipBigrams = args.Exists("skipbigrams");

	TSynanHttpServer Server;
	try {
        GlobalLoadMorphHolder(morphRussian);
        GlobalLoadMorphHolder(morphGerman);
        GlobalLoadMorphHolder(morphEnglish);
        GlobalLoadMorphHolder(morphUkrainian);
        try {
            GlobalLoadMorphHolder(morphSpanish);
        } catch (std::exception& e) {
            LOGE << "Failed to load Spanish Morphology: " << e.what();
        }
        try {
            GlobalLoadMorphHolder(morphLatin);
        } catch (std::exception& e) {
            LOGE << "Failed to load Latin Morphology: " << e.what();
        }
        try {
            GlobalLoadMorphHolder(morphFrench);
        } catch (std::exception& e) {
            LOGE << "Failed to load French Morphology: " << e.what();
        }
        try {
            GlobalLoadMorphHolder(morphPortuguese);
        } catch (std::exception& e) {
            LOGE << "Failed to load Portuguese Morphology: " << e.what();
        }
        try {
            GlobalLoadMorphHolder(morphFinnish);
        } catch (std::exception& e) {
            LOGE << "Failed to load Finnish Morphology: " << e.what();
        }
		DealWithLockFile("SynanDaemon.lck");
		Server.Initialize(args.Retrieve("host"), atoi(args.Retrieve("port").c_str()));
		Server.LoadSynan(!skipBigrams);
		Server.Start();
	}
	catch (std::exception& c)
	{
		LOGE << c.what() << "\n";
		return 1;
	}
	catch(...)
	{
        LOGE << "General exception";
		return 1;
	};
	return 0;
}




