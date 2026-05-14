#pragma once

#include "synan/SynCommonLib/FormatCaller.h"

class CUkrFormatCaller : public CFormatCaller
{
public:
    CUkrFormatCaller(const class CUkrSyntaxOpt* pOpt);
    void AddSimpleSimilarRules() override {}
    void AddAllRules() override {}
    void BuildOborotGroups() override {}
    int GetRuleByGroupTypeForThesaurus(int GroupType) const override { return -1; }
};
