#include "SpaSentence.h"
#include "SpaSyntaxOpt.h"
#include "SpaFormatCaller.h"

CSpaSentence::CSpaSentence(const CSyntaxOpt* opt) : CSentence(opt)
{
}

CSpaSentence::~CSpaSentence()
{
}

void CSpaSentence::ReadNextFromPlmLinesLanguageSpecific()
{
}

void CSpaSentence::BuildSubjAndPredRelation(CMorphVariant& synVariant, long RootWordNo, EClauseType ClauseType)
{
	synVariant.ResetSubj();

	long iPred = RootWordNo;
	if (iPred >= 0 && iPred < (long)synVariant.m_SynUnits.size()) {
		const CSynUnit& PU = synVariant.m_SynUnits[iPred];
		const CSynWord& PW = m_Words[PU.m_SentPeriod.m_iFirstWord];
		if (!PW.m_Homonyms.empty() && PU.m_iHomonymNum < (int)PW.m_Homonyms.size()) {
			const CSynHomonym& PH = PW.m_Homonyms[PU.m_iHomonymNum];
			if (!GetSpaGramTab()->is_verb_form(PH.m_iPoses)) {
				iPred = -1;
			}
		}
	}

	if (iPred == -1 || iPred >= (long)synVariant.m_SynUnits.size()) {
		for (long i = 0; i < (long)synVariant.m_SynUnits.size(); i++) {
			const CSynUnit& U = synVariant.m_SynUnits[i];
			if (U.m_Type != EWord) continue;
			const CSynWord& W = m_Words[U.m_SentPeriod.m_iFirstWord];
			if (W.m_Homonyms.empty() || U.m_iHomonymNum >= (int)W.m_Homonyms.size()) continue;
			const CSynHomonym& H = W.m_Homonyms[U.m_iHomonymNum];
			if (GetSpaGramTab()->is_verb_form(H.m_iPoses)) {
				iPred = i;
				break;
			}
		}
	}

	if (iPred == -1 || iPred >= (long)synVariant.m_SynUnits.size()) return;
	synVariant.m_iPredk = iPred;

	const CSynUnit& PU = synVariant.m_SynUnits[iPred];
	const CSynWord& PW = m_Words[PU.m_SentPeriod.m_iFirstWord];
	if (PW.m_Homonyms.empty() || PU.m_iHomonymNum >= (int)PW.m_Homonyms.size()) return;
	const CSynHomonym& PH = PW.m_Homonyms[PU.m_iHomonymNum];

	// Normal SVO (Subject before verb) - Backward scan
	for (long i = iPred - 1; i >= 0; i--) {
		const CSynUnit& U = synVariant.m_SynUnits[i];
		if (U.m_Type != EWord) continue;

		const CSynWord& W = m_Words[U.m_SentPeriod.m_iFirstWord];
		if (W.m_Homonyms.empty() || U.m_iHomonymNum >= (int)W.m_Homonyms.size()) continue;
		const CSynHomonym& H = W.m_Homonyms[U.m_iHomonymNum];

		if (GetSpaGramTab()->IsMorphNoun(H.m_iPoses) ||
		    GetSpaGramTab()->is_morph_pronoun(H.m_iPoses)) {

			if (GetSpaGramTab()->GleicheSubjectPredicate(H.GetGramCodes().c_str(), PH.GetGramCodes().c_str())) {
				synVariant.m_Subjects.push_back(i);
				synVariant.m_bGoodSubject = true;
				break;
			}
		}
	}

	// Inverted subjects (Subject after verb) - Forward scan
	if (!synVariant.m_bGoodSubject) {
		for (long i = iPred + 1; i < (long)synVariant.m_SynUnits.size(); i++) {
			const CSynUnit& U = synVariant.m_SynUnits[i];
			if (U.m_Type != EWord) continue;

			const CSynWord& W = m_Words[U.m_SentPeriod.m_iFirstWord];
			if (W.m_Homonyms.empty() || U.m_iHomonymNum >= (int)W.m_Homonyms.size()) continue;
			const CSynHomonym& H = W.m_Homonyms[U.m_iHomonymNum];

			if (GetSpaGramTab()->IsMorphNoun(H.m_iPoses) ||
			    GetSpaGramTab()->is_morph_pronoun(H.m_iPoses)) {

				if (GetSpaGramTab()->GleicheSubjectPredicate(H.GetGramCodes().c_str(), PH.GetGramCodes().c_str())) {
					synVariant.m_Subjects.push_back(i);
					synVariant.m_bGoodSubject = true;
					break;
				}
			}
		}
	}
}

int CSpaSentence::GetCountOfStrongRoots(const CClause& C, const CMorphVariant& synVar) const
{
	return 1;
}

bool CSpaSentence::WordSchemeEqForThesaurus(const CSynHomonym& Homonym, const CSynPlmLine& word_scheme) const
{
	return false;
}

bool CSpaSentence::RunSyntaxInClauses(ESynRulesSet type)
{
	try {
		if (m_pSyntaxOptions == NULL) return false;
		int count = GetClausesCount();
		for (int i = 0; i < count; i++) {
			BuildGLRGroupsInClause(GetClause(i));
		}
		return true;
	}
	catch (...) {
		return false;
	}
}

void CSpaSentence::AfterBuildGroupsTrigger(CClause& C)
{
}

CFormatCaller* CSpaSentence::GetNewFormatCaller() const
{
	return new CSpaFormatCaller(GetOpt());
}

bool CSpaSentence::BuildClauses()
{
	m_bPanicMode = IsPanicSentence();
	assert(GetClausesCount() == 0);
	FindGraPairs();

	if (!BuildInitialClauses()) {
		return false;
	}

	RunSyntaxInClauses(AllRules);
	AssignClauseNoToWords();
	return true;
}

void CSpaSentence::InitHomonymMorphInfo(CSynHomonym& H)
{
	H.InitAncodePattern();
}

void CSpaSentence::InitHomonymLanguageSpecific(CSynHomonym& H, const CLemWord* pWord)
{
}

void CSpaSentence::SolveAmbiguityUsingRuleForTwoPredicates(int iFirstWord, int iLastWord)
{
}

void CSpaSentence::ChooseClauseType(const std::vector<SClauseType>& vectorTypes, CMorphVariant& V)
{
	V.m_ClauseTypeNo = 0;
}

bool CSpaSentence::SetClauseBorderIfThereAreTwoPotentialPredicates(int FWrd, int LWrd)
{
	return false;
}

bool CSpaSentence::IsInitialClauseType(EClauseType ClauseType) const
{
	return true;
}

bool CSpaSentence::IsRelativSentencePronoun(int ClauseStartWordNo, int WordNo, int& HomonymNo) const
{
	return false;
}

bool CSpaSentence::AllHomonymsArePredicates(const CSynWord& W) const
{
	for (size_t i = 0; i < W.m_Homonyms.size(); i++) {
		if (!GetSpaGramTab()->is_verb_form(W.m_Homonyms[i].m_iPoses))
			return false;
	}
	return !W.m_Homonyms.empty();
}

bool CSpaSentence::CanBeRelativeAntecedent(const CSynHomonym& H) const
{
	return GetSpaGramTab()->IsMorphNoun(H.m_iPoses);
}

bool CSpaSentence::IsProfession(const CSynHomonym& H) const
{
	return false;
}

EClauseType CSpaSentence::GetClauseTypeByAncodePattern(const CAncodePattern& Pattern) const
{
	return (EClauseType)0;
}
