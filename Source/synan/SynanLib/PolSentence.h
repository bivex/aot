#pragma once

#include "synan/SynCommonLib/Sentence.h"
#include "PolSyntaxOpt.h"

class CPolSentence : public CSentence
{
public:
	CPolSentence(const class CSyntaxOpt* m_pSyntaxOptions);
	~CPolSentence();
	void ReadNextFromPlmLinesLanguageSpecific() override;
	void BuildSubjAndPredRelation(CMorphVariant& synVariant, long RootWordNo, EClauseType ClauseType) override;
	int  GetCountOfStrongRoots(const class CClause& C, const CMorphVariant& synVar) const override;
	bool WordSchemeEqForThesaurus(const CSynHomonym& Homonym, const CSynPlmLine& word_scheme) const override;
	bool RunSyntaxInClauses(ESynRulesSet type) override;
	void AfterBuildGroupsTrigger(class CClause& C) override;
	const CPolSyntaxOpt* GetOpt() const { return (const CPolSyntaxOpt*)m_pSyntaxOptions; }
	const CPolGramTab* GetPolGramTab() const { return (const CPolGramTab*)GetOpt()->GetGramTab(); }
	CFormatCaller* GetNewFormatCaller() const override;
	bool BuildClauses() override;
	void InitHomonymMorphInfo(CSynHomonym& H) override;
	void InitHomonymLanguageSpecific(CSynHomonym& H, const CLemWord* pWord) override;
	void SolveAmbiguityUsingRuleForTwoPredicates(int iFirstWord, int iLastWord) override;
	void ChooseClauseType(const std::vector<SClauseType>& vectorTypes, CMorphVariant& V) override;
	bool CheckLastPredicatePosition(size_t ClauseLastWordNo, long RootWordNo) const override { return true; }
	void CloneHomonymsForOborots() override {}
	bool SetClauseBorderIfThereAreTwoPotentialPredicates(int FWrd, int LWrd) override;
	bool IsInitialClauseType(EClauseType ClauseType) const override;
	bool IsRelativSentencePronoun(int ClauseStartWordNo, int WordNo, int& HomonymNo) const override;
	bool AllHomonymsArePredicates(const CSynWord& W) const override;
	bool CanBeRelativeAntecedent(const CSynHomonym& H) const override;
	bool IsProfession(const CSynHomonym& H) const override;
	EClauseType GetClauseTypeByAncodePattern(const CAncodePattern& Pattern) const override;
};
