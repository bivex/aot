#pragma once

#include "synan/SynCommonLib/ThesaurusForSyntax.h"

class CUkrThesaurusForSyntax : public CThesaurusForSyntax
{
public:
    CUkrThesaurusForSyntax(const class CSyntaxOpt* Opt) : CThesaurusForSyntax(Opt) {}
protected:
    void AssignMainGroupsToModel(class CGroups& model, const class CInnerModel& piModel) override {}
};
