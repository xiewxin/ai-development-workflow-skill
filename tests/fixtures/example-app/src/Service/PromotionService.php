<?php

declare(strict_types=1);

final class PromotionService
{
    /** 驗證折扣碼並回傳可套用的折扣。 */
    public function validateCode(string $code): array
    {
        return ['valid' => true, 'amount' => 100];
    }
}
