#pragma once

#include "synan/SynCommonLib/FormatCaller.h"

class CLatFormatCaller : public CFormatCaller
{
public:
    CLatFormatCaller(const class CSyntaxOpt* pOpt) : CFormatCaller(pOpt) {}
    void AddSimpleSimilarRules() override {}
    void AddAllRules() override {}
    void BuildOborotGroups() override {}
    int GetRuleByGroupTypeForThesaurus(int GroupType) const override { return -1; }
};
