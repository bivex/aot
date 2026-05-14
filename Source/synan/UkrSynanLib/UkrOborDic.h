#pragma once

#include "synan/SynCommonLib/oborot.h"

class CUkrOborDic : public COborDic 
{
public:
	CUkrOborDic(const class CSyntaxOpt* Opt);
protected:
	bool ReadOborDic(const class CDictionary* piOborDic) override { return true; }
};
