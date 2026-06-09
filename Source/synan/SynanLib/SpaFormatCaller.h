#pragma once

#include "synan/SynCommonLib/FormatCaller.h"

class CSpaFormatCaller : public CFormatCaller
{
public:
    CSpaFormatCaller(const class CSyntaxOpt* pOpt) : CFormatCaller(pOpt) {}
    void AddSimpleSimilarRules() override {}
    void AddAllRules() override {}
    void BuildOborotGroups() override {}
    int GetRuleByGroupTypeForThesaurus(int GroupType) const override { return -1; }
};
